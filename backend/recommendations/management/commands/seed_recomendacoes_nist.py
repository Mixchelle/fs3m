from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from collections import defaultdict
import json
from datetime import date

from users.models import CustomUser
from responses.models import Submission, Answer
from frameworks.models import Question
from recommendations.models import Recomendacao


# Catálogo base por controle (exemplos; pode ampliar à vontade)
NIST_RECO_CATALOG = {
    "DE.AE-02": {
        "nome": "Aprimorar análise de eventos adversos",
        "detalhes": "Implantar correlação/enriquecimento de eventos e ampliar playbooks.",
        "investimentos": "SIEM/SOAR, horas de consultoria",
        "riscos": "Detecção tardia e impacto ampliado",
        "justificativa": "Maturidade abaixo do nível-alvo (>=3).",
        "prioridade": "alta",
        "meses": 3,
    },
    "DE.AE-03": {
        "nome": "Melhorar correlação multi-fonte",
        "detalhes": "Normalizar logs, unificar taxonomias e criar regras entre fontes.",
        "investimentos": "SIEM, conectores, consultoria",
        "riscos": "Falsos positivos/negativos elevados",
        "justificativa": "Cobertura insuficiente e baixa maturidade.",
        "prioridade": "media",
        "meses": 4,
    },
    # acrescente outros códigos NIST aqui...
}

FUNC_TO_CATEGORIA = {
    "GV": "Governar (GV)",
    "ID": "Identificar (ID)",
    "PR": "Proteger (PR)",
    "DE": "Detectar (DE)",
    "RS": "Responder (RS)",
    "RC": "Recuperar (RC)",
}

MAPA_TEXTO_NUM = {
    "Inicial": Decimal("1"),
    "Repetido": Decimal("2"),
    "Definido": Decimal("3"),
    "Gerenciado": Decimal("4"),
    "Otimizado": Decimal("5"),
}


def _to_decimal(val):
    if val is None:
        return None
    if isinstance(val, (int, float, Decimal)):
        return Decimal(str(val))
    # pode vir em Answer.value como json/str
    s = str(val).strip()
    if s in MAPA_TEXTO_NUM:
        return MAPA_TEXTO_NUM[s]
    # tentar extrair {"value": X}
    try:
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            data = json.loads(s)
            if isinstance(data, dict) and "value" in data:
                return _to_decimal(data["value"])
    except Exception:
        pass
    try:
        return Decimal(s)
    except Exception:
        return None


def _ans_to_score(ans):
    # 1) tenta score numérico
    if getattr(ans, "score", None) is not None:
        try:
            return Decimal(str(ans.score))
        except Exception:
            pass
    # 2) tenta em value/value.value
    v = getattr(ans, "value", None)
    if isinstance(v, dict) and "value" in v:
        return _to_decimal(v["value"])
    return _to_decimal(v)


def _add_months(d: date, months: int) -> date:
    """Adicionar meses sem depender de dateutil."""
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    # último dia do mês alvo
    from calendar import monthrange
    last = monthrange(y, m)[1]
    return date(y, m, min(d.day, last))


class Command(BaseCommand):
    help = "Gera recomendações NIST para submissions onde política/prática/score < 3."

    def add_arguments(self, parser):
        parser.add_argument("--submission-id", type=int, help="ID específico do Submission.")
        parser.add_argument("--only-new", action="store_true", help="Não tocar nas já existentes.")
        parser.add_argument("--force", action="store_true", help="Apaga e recria para o submission alvo.")
        parser.add_argument("--template-slug", type=str, default="nist-csf-2-pt-maturidade",
                            help="Filtrar submissions por template.slug (default: nist-csf-2-pt-maturidade)")

    @transaction.atomic
    def handle(self, *args, **opts):
        sub_id = opts.get("submission_id")
        only_new = bool(opts.get("only_new"))
        force = bool(opts.get("force"))
        template_slug = opts.get("template_slug") or "nist-csf-2-pt-maturidade"

        # alvo
        subs = Submission.objects.select_related("customer", "template", "framework")
        subs = subs.filter(template__slug=template_slug)
        if sub_id:
            subs = subs.filter(id=sub_id)

        total_created = 0
        today = timezone.now().date()
        # no topo do handle(), logo após today = timezone.now().date()
        analista_default = (
            CustomUser.objects.filter(email="analista@fs3m.com").first()
            or CustomUser.objects.filter(role__in=["analista", "admin"]).first()
        )
        if not analista_default:
            analista_default = CustomUser.objects.create_user(
                email="analista@fs3m.com",
                password="changeme123",
                nome="Analista Padrão",
                role="analista",
            )


        for sub in subs:
            cliente = sub.customer

            if force:
                Recomendacao.objects.filter(submission=sub).delete()

            # coletar respostas por controle
            per_ctl = defaultdict(lambda: {
                "func": None,
                "policy": None, "practice": None, "score": None,
                "qids": {},  # local_code -> question.id
                "title": None,
            })

            answers = (
                Answer.objects
                .filter(submission=sub)
                .select_related("question__control__domain")
            )

            for ans in answers:
                q = ans.question
                if not q or not q.control:
                    continue
                ctl = q.control
                dom = ctl.domain
                code = ctl.code  # ex: "DE.AE-02"
                cat = code.split("-")[0]  # "DE.AE"
                func = cat.split(".")[0]  # "DE"

                bucket = per_ctl[code]
                bucket["func"] = func
                bucket["title"] = ctl.title or code
                lc = (q.local_code or "").strip()

                if lc in ("politica", "politica_pt", "policy"):
                    bucket["policy"] = _ans_to_score(ans)
                    bucket["qids"][lc] = q.id
                elif lc in ("pratica", "pratica_pt", "practice"):
                    bucket["practice"] = _ans_to_score(ans)
                    bucket["qids"][lc] = q.id
                elif lc in ("score",):
                    bucket["score"] = _ans_to_score(ans)
                    bucket["qids"][lc] = q.id

            # criar recomendações conforme < 3
            for ctl_code, rec in per_ctl.items():
                func = rec["func"] or ctl_code.split(".")[0]
                categoria_display = FUNC_TO_CATEGORIA.get(func, "Governar (GV)")
                base = NIST_RECO_CATALOG.get(ctl_code, {
                    "nome": f"Elevar maturidade do controle {ctl_code}",
                    "detalhes": "Formalizar política e prática para atingir maturidade 3.",
                    "investimentos": "Horas de processo; ajustes de ferramenta",
                    "riscos": "Exposição a riscos acima do apetite",
                    "justificativa": "Maturidade abaixo do nível-alvo (>=3).",
                    "prioridade": "media",
                    "meses": 3,
                })

                alvos = []
                if rec["policy"] is not None and rec["policy"] < Decimal("3"):
                    alvos.append(("Política", rec["policy"], rec["qids"].get("politica") or rec["qids"].get("policy")))
                if rec["practice"] is not None and rec["practice"] < Decimal("3"):
                    alvos.append(("Prática", rec["practice"], rec["qids"].get("pratica") or rec["qids"].get("practice")))
                # opcional: disparar genérica se só o score < 3
                if not alvos and rec["score"] is not None and rec["score"] < Decimal("3"):
                    alvos.append(("Ambas", rec["score"], rec["qids"].get("score")))

                for aplicabilidade, nota, qid in alvos:
                    # evitar duplicata
                    exists = Recomendacao.objects.filter(
                        submission=sub, nist=ctl_code, aplicabilidade=aplicabilidade
                    ).exists()
                    if only_new and exists:
                        continue
                    if (not only_new) and exists:
                        # idempotência básica: apaga e recria este par
                        Recomendacao.objects.filter(
                            submission=sub, nist=ctl_code, aplicabilidade=aplicabilidade
                        ).delete()

                    meses = int(base["meses"])
                    fim = _add_months(today, meses)
                    prioridade = base["prioridade"]
                    if nota is not None and nota <= 2:
                        prioridade = "alta"

                    Recomendacao.objects.create(
                        cliente=cliente,
                        submission=sub,
                        analista=analista_default,
                        nome=base["nome"],
                        categoria=categoria_display,
                        aplicabilidade=aplicabilidade,
                        tecnologia="Agnóstico",
                        nist=ctl_code,
                        prioridade=prioridade,
                        responsavel="Não definido",
                        data_inicio=today,
                        data_fim=fim,
                        meses=meses,
                        detalhes=base["detalhes"],
                        investimentos=base["investimentos"],
                        riscos=base["riscos"],
                        justificativa=base["justificativa"],
                        observacoes="Gerada automaticamente (nota < 3).",
                        urgencia="4" if (nota is not None and nota <= 2) else "3",
                        gravidade="4" if (nota is not None and nota <= 2) else "3",
                        perguntaId=str(qid) if qid else ctl_code,
                    )
                    total_created += 1

        self.stdout.write(self.style.SUCCESS(f"Recomendações criadas: {total_created}"))

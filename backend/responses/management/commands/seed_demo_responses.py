# responses/management/commands/seed_fill_existing.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal
import random

from frameworks.models import FormTemplate, Question, ChoiceOption
from responses.models import Submission, Answer

User = get_user_model()


class Command(BaseCommand):
    help = (
        "APAGA todas as Submissions (e respostas) dos clientes selecionados para os templates alvo "
        "e CRIA uma única nova Submission por cliente por template, preenchendo automaticamente."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--all-templates",
            action="store_true",
            help="Usa todos os FormTemplate (não apenas active=True).",
        )
        parser.add_argument(
            "--only-emails",
            type=str,
            help=(
                "Lista de e-mails separados por vírgula para limitar os clientes. "
                "Ex.: --only-emails=a@b.com,c@d.com"
            ),
        )
        parser.add_argument(
            "--leave-missing",
            type=int,
            default=0,
            help="Deixa N perguntas sem responder por submission (p/ testes). Padrão: 0 (responde todas).",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        use_all = opts.get("all_templates") is True
        only_emails = opts.get("only_emails")
        leave_missing = max(0, int(opts.get("leave_missing") or 0))

        # -----------------------
        # Templates alvo
        # -----------------------
        if use_all:
            templates = FormTemplate.objects.all().select_related("framework")
        else:
            templates = FormTemplate.objects.filter(active=True).select_related("framework")
            if not templates.exists():
                templates = FormTemplate.objects.all().select_related("framework")

        if not templates.exists():
            raise SystemExit("Nenhum FormTemplate encontrado no banco.")

        # -----------------------
        # Clientes (usuários com role de cliente, se existir)
        # -----------------------
        qs_users = User.objects.filter(is_active=True)

        # Filtra por role, se o campo existir
        try:
            User._meta.get_field("role")
            qs_users = qs_users.filter(role__in=["cliente", "client"])
        except Exception:
            # Campo 'role' pode não existir
            pass

        # Filtra por e-mails, se fornecido
        if only_emails:
            emails = [e.strip() for e in only_emails.split(",") if e.strip()]
            qs_users = qs_users.filter(email__in=emails)

        clientes = list(qs_users)
        if not clientes:
            raise SystemExit("Nenhum cliente ativo encontrado para processar.")

        # -----------------------
        # Um analista (opcional para assigned_to)
        # -----------------------
        analista = None
        try:
            User._meta.get_field("role")
            analista = User.objects.filter(role__in=["analista", "analyst"]).first()
        except Exception:
            analista = None

        # -----------------------
        # DROP: apaga Submissions/Answers existentes dos clientes selecionados
        #       para os templates alvo
        # -----------------------
        subs_qs = Submission.objects.filter(customer__in=clientes, template__in=templates)
        old_count = subs_qs.count()
        self.stdout.write(self.style.WARNING(f"Apagando {old_count} submissions anteriores (e suas respostas)…"))
        # Answers caem por CASCADE, se FK estiver configurada corretamente
        subs_qs.delete()

        total_answers = 0
        total_submissions = 0

        # -----------------------
        # Recria UMA nova submission por cliente por template + preenche respostas
        # -----------------------
        for cli in clientes:
            self.stdout.write(self.style.SUCCESS(f"Cliente: {cli.email}"))
            for template in templates:
                # Cria nova submission do zero
                sub = Submission.objects.create(
                    customer=cli,
                    template=template,
                    framework=template.framework,
                    version=1,              # como apagamos tudo, reinicia em 1
                    status="draft",
                    assigned_to=analista,
                )
                total_submissions += 1
                self.stdout.write(f"  Nova submission criada para {template.slug}")

                # Perguntas do template
                qset = Question.objects.filter(control__in=template.controls.all()).order_by("id")
                qcount = qset.count()
                if qcount == 0:
                    self.stdout.write(self.style.WARNING("    Nenhuma pergunta neste template. Pulando."))
                    continue

                # Se for para deixar N sem responder, sorteia quais ficam sem resposta
                skip_indices = set()
                if leave_missing > 0 and leave_missing < qcount:
                    all_indices = list(range(qcount))
                    random.shuffle(all_indices)
                    skip_indices = set(all_indices[:leave_missing])

                for idx, q in enumerate(qset):
                    if idx in skip_indices:
                        continue  # deixa sem resposta para teste

                    # 1) Se houver ChoiceOption, escolhe uma
                    opts = list(ChoiceOption.objects.filter(question=q))
                    if opts:
                        pick = random.choice(opts)
                        Answer.objects.update_or_create(
                            submission=sub,
                            question=q,
                            defaults={
                                "value": {"type": "choice", "value": pick.value},
                                "score": (
                                    Decimal(str(pick.weight))
                                    if pick.weight is not None
                                    else None
                                ),
                                "evidence": f"Opção escolhida: {pick.value} (seed).",
                            },
                        )
                        total_answers += 1
                        continue

                    # 2) Heurísticas por local_code comuns
                    lc = (q.local_code or "").lower()
                    if lc in {"score", "politica", "pratica"}:
                        val = random.randint(1, 5)
                        Answer.objects.update_or_create(
                            submission=sub,
                            question=q,
                            defaults={
                                "value": {"type": "scale", "value": val},
                                "score": Decimal(str(val)),
                                "evidence": f"Seed {lc} nível {val}.",
                            },
                        )
                        total_answers += 1
                        continue

                    if lc in {"evidence", "info"}:
                        Answer.objects.update_or_create(
                            submission=sub,
                            question=q,
                            defaults={
                                "value": {"type": "text", "value": f"Texto automático para {lc} (seed)."},
                                "evidence": f"Registro de {lc} (seed).",
                            },
                        )
                        total_answers += 1
                        continue

                    if lc == "attachment":
                        Answer.objects.update_or_create(
                            submission=sub,
                            question=q,
                            defaults={
                                "value": {"type": "file", "value": None},
                                "evidence": "Anexo será enviado via API (exemplo).",
                            },
                        )
                        total_answers += 1
                        continue

                    # 3) Fallback genérico: texto (mais seguro)
                    Answer.objects.update_or_create(
                        submission=sub,
                        question=q,
                        defaults={
                            "value": {"type": "text", "value": "Resposta automática (seed)."},
                            "evidence": "Gerado pelo seed genérico.",
                            "score": None,
                        },
                    )
                    total_answers += 1

                # Recalcula o progresso desta submission
                if hasattr(sub, "recalc_progress"):
                    sub.recalc_progress(commit=True)

        self.stdout.write(
            self.style.SUCCESS(
                f"OK! Apagadas {old_count} submissions antigas. "
                f"Criadas {total_submissions} novas submissions e {total_answers} respostas."
            )
        )

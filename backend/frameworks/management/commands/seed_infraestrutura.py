# backend/frameworks/management/commands/seed_infraestrutura.py
from django.core.management.base import BaseCommand
from django.db import transaction

from frameworks.models import (
    Framework,
    Domain,
    Control,
    Question,
    ChoiceOption,
    ScoringModel,
    FormTemplate,
    TemplateItem,
)


class Command(BaseCommand):
    help = "Cria o framework 'Infraestrutura' com domínios, controles e template básicos."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Criando framework de Infraestrutura...")

        # ---------- Scoring model (Sim/Parcial/Não/N.A.) ----------
        scoring, _ = ScoringModel.objects.get_or_create(
            slug="yes-partial-no-na",
            defaults={
                "name": "Yes/Partial/No/N.A.",
                "mapping": {"yes": 100, "partial": 50, "no": 0, "na": None},
                "rules": {"hint": "Pontuação padrão para perguntas de infraestrutura."},
            },
        )

        # ---------- Framework ----------
        framework, _ = Framework.objects.get_or_create(
            slug="infraestrutura-pt",
            defaults={
                "name": "Infraestrutura (PT-BR)",
                "version": "1.0",
                "description": "Controles de infraestrutura (rede, servidores, backup, monitoramento).",
                "active": True,
                "editable": True,
            },
        )

        # ---------- Domínios ----------
        domains_def = [
            ("NET", "Rede"),
            ("SRV", "Servidores & SO"),
            ("BKP", "Backup & Recuperação"),
            ("MON", "Monitoramento & Logs"),
        ]
        domains = {}
        for idx, (code, title) in enumerate(domains_def):
            d, _ = Domain.objects.get_or_create(
                framework=framework,
                code=code,                       # <- use code para buscar
                defaults={"title": title, "order": idx},
            )
            # garante atualização de título/ordem se já existia
            if d.title != title or d.order != idx:
                d.title = title
                d.order = idx
                d.save(update_fields=["title", "order"])
            domains[code] = d

        # ---------- Controles (exemplo inicial) ----------
        controls_def = {
            "NET": [
                ("NET.FW-01", "Firewalls configurados com política de mínimo privilégio"),
                ("NET.VLAN-01", "Segmentação de rede por VLANs e ACLs"),
                ("NET.VPN-01", "Acesso remoto via VPN com MFA"),
            ],
            "SRV": [
                ("SRV.PATCH-01", "Gerenciamento de patches atualizado"),
                ("SRV.HARD-01", "Endurecimento (hardening) de SO e serviços"),
                ("SRV.ANTI-01", "Proteção antimalware/EDR implantada"),
            ],
            "BKP": [
                ("BKP.POL-01", "Política de backup documentada e aplicada"),
                ("BKP.TEST-01", "Testes periódicos de restauração"),
                ("BKP.OFF-01", "Cópias offsite/imutáveis (3-2-1)"),
            ],
            "MON": [
                ("MON.LOG-01", "Coleta centralizada de logs (SIEM/ELK)"),
                ("MON.ALERT-01", "Alertas configurados e acionáveis"),
                ("MON.NTA-01", "Análise de tráfego/NetFlow/NDR"),
            ],
        }

        created_controls = 0
        for dom_code, items in controls_def.items():
            domain = domains[dom_code]
            for idx, (code, title) in enumerate(items):
                control, _ = Control.objects.get_or_create(
                    framework=framework,
                    code=code,
                    defaults={
                        "domain": domain,
                        "title": title,
                        "description": "",
                        "order": idx,
                        "active": True,
                    },
                )
                # atualiza domínio/ordem se necessário
                update_fields = []
                if control.domain_id != domain.id:
                    control.domain = domain
                    update_fields.append("domain")
                if control.order != idx:
                    control.order = idx
                    update_fields.append("order")
                if update_fields:
                    control.save(update_fields=update_fields)
                created_controls += 1

                # Pergunta 1 (escala categórica yes/partial/no/na)
                q1, _ = Question.objects.get_or_create(
                    control=control,
                    local_code="status",
                    defaults={
                        "prompt": "Status do controle",
                        "type": "choice",
                        "required": True,
                        "order": 0,
                        "meta": {"style": "radio"},
                        "scoring_model": scoring,
                    },
                )
                if q1.scoring_model_id is None:
                    q1.scoring_model = scoring
                    q1.save(update_fields=["scoring_model"])

                ChoiceOption.objects.get_or_create(
                    question=q1, value="yes", defaults={"label": "Sim", "weight": 100, "order": 1}
                )
                ChoiceOption.objects.get_or_create(
                    question=q1, value="partial", defaults={"label": "Parcial", "weight": 50, "order": 2}
                )
                ChoiceOption.objects.get_or_create(
                    question=q1, value="no", defaults={"label": "Não", "weight": 0, "order": 3}
                )
                ChoiceOption.objects.get_or_create(
                    question=q1, value="na", defaults={"label": "N.A.", "weight": None, "order": 4}
                )

                # Pergunta 2 (texto livre / evidências)
                Question.objects.get_or_create(
                    control=control,
                    local_code="evidence",
                    defaults={
                        "prompt": "Evidências/observações",
                        "type": "text",
                        "required": False,
                        "order": 1,
                        "meta": {"placeholder": "Descreva evidências, links, prints, procedimentos, etc."},
                    },
                )

        # ---------- Template ----------
        template, _ = FormTemplate.objects.get_or_create(
            slug="infraestrutura-basico",
            defaults={
                "name": "Infraestrutura - Básico",
                "framework": framework,
                "version": "1.0",
                "description": "Template com controles básicos de infraestrutura.",
                "active": True,
                "editable": True,
            },
        )

        # monta o template com todos os controles em ordem por domínio
        TemplateItem.objects.filter(template=template).delete()
        order_counter = 0
        for dom_code in [d[0] for d in domains_def]:
            qs = Control.objects.filter(framework=framework, domain=domains[dom_code]).order_by("order", "code")
            for control in qs:
                TemplateItem.objects.get_or_create(
                    template=template,
                    control=control,
                    question=None,
                    defaults={"order": order_counter},
                )
                order_counter += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"OK! Framework='{framework.name}', domínios={len(domains)}, controles={created_controls}, template='{template.name}'."
            )
        )

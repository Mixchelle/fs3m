from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal
import random
from collections import defaultdict

from frameworks.models import FormTemplate, Question, ChoiceOption
from responses.models import Submission, Answer

User = get_user_model()


class Command(BaseCommand):
    help = "Cria Submissions e Answers de exemplo para NIST e Infraestrutura para 3 clientes."

    @transaction.atomic
    def handle(self, *args, **options):
        # templates necessários
        try:
            t_nist = FormTemplate.objects.get(slug="nist-csf-2-pt-maturidade")
            t_infra = FormTemplate.objects.get(slug="infraestrutura-basico")
        except FormTemplate.DoesNotExist as e:
            raise SystemExit(
                "Templates não encontrados. Rode antes: seed_nist_pt e seed_infraestrutura."
            ) from e

        # clientes
        clientes = list(
            User.objects.filter(
                email__in=[
                    "cliente1@empresa.com",
                    "cliente2@empresa.com",
                    "cliente3@empresa.com",
                ]
            )
        )
        if not clientes:
            raise SystemExit("Nenhum cliente encontrado. Rode antes: seed_users.")

        # um analista (opcional para assigned_to)
        analista = User.objects.filter(email="analista@fs3m.com").first()

        total_answers = 0
        for cli in clientes:
            for template in (t_nist, t_infra):
                sub, created = Submission.objects.get_or_create(
                    customer=cli,
                    template=template,
                    framework=template.framework,
                    version=1,
                    defaults={
                        "status": "draft",
                        "assigned_to": analista,
                    },
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Submission criada: {cli.email} / {template.slug}"
                        )
                    )
                else:
                    self.stdout.write(
                        f"Submission já existia: {cli.email} / {template.slug}"
                    )

                # Preencher respostas conforme o template
                if template.slug == "nist-csf-2-pt-maturidade":
                    qs = (
                        Question.objects.filter(control__in=template.controls.all())
                        .select_related("control")
                    )
                    by_control = defaultdict(dict)
                    for q in qs:
                        by_control[q.control_id][q.local_code] = q

                    for control_id, qmap in by_control.items():
                        # score
                        q = qmap.get("score")
                        if q:
                            val = random.randint(1, 5)
                            Answer.objects.update_or_create(
                                submission=sub,
                                question=q,
                                defaults={
                                    "value": {"type": "scale", "value": val},
                                    "score": Decimal(str(val)),
                                    "evidence": f"Seed score nível {val}.",
                                },
                            )
                            total_answers += 1

                        # politica
                        q = qmap.get("politica")
                        if q:
                            val = random.randint(1, 5)
                            Answer.objects.update_or_create(
                                submission=sub,
                                question=q,
                                defaults={
                                    "value": {"type": "scale", "value": val},
                                    "score": Decimal(str(val)),
                                    "evidence": f"Seed política nível {val}.",
                                },
                            )
                            total_answers += 1

                        # pratica
                        q = qmap.get("pratica")
                        if q:
                            val = random.randint(1, 5)
                            Answer.objects.update_or_create(
                                submission=sub,
                                question=q,
                                defaults={
                                    "value": {"type": "scale", "value": val},
                                    "score": Decimal(str(val)),
                                    "evidence": f"Seed prática nível {val}.",
                                },
                            )
                            total_answers += 1

                        # evidence
                        q = qmap.get("evidence")
                        if q:
                            Answer.objects.update_or_create(
                                submission=sub,
                                question=q,
                                defaults={
                                    "value": {"type": "text", "value": "Evidências complementares (seed)."},
                                    "evidence": "Registro de evidências (seed).",
                                },
                            )
                            total_answers += 1

                        # info
                        q = qmap.get("info")
                        if q:
                            Answer.objects.update_or_create(
                                submission=sub,
                                question=q,
                                defaults={
                                    "value": {"type": "text", "value": "Notas e links (seed)."},
                                    "evidence": "Informações complementares cadastradas pelo seed.",
                                },
                            )
                            total_answers += 1

                        # attachment
                        q = qmap.get("attachment")
                        if q:
                            Answer.objects.update_or_create(
                                submission=sub,
                                question=q,
                                defaults={
                                    "value": {"type": "file", "value": None},
                                    "evidence": "Anexo será enviado via API (exemplo).",
                                },
                            )
                            total_answers += 1

                elif template.slug == "infraestrutura-basico":
                    qset = (
                        Question.objects.filter(control__in=template.controls.all())
                        .select_related("control")
                    )
                    for q in qset:
                        if q.local_code == "status":
                            choice_pool = ["yes", "partial", "no", "na"]
                            pick = random.choice(choice_pool)
                            weight = None
                            try:
                                opt = ChoiceOption.objects.get(question=q, value=pick)
                                weight = opt.weight
                            except ChoiceOption.DoesNotExist:
                                pass

                            Answer.objects.update_or_create(
                                submission=sub,
                                question=q,
                                defaults={
                                    "value": {"type": "choice", "value": pick},
                                    "score": (
                                        Decimal(str(weight))
                                        if weight is not None
                                        else None
                                    ),
                                    "evidence": f"Status {pick} (seed).",
                                },
                            )
                            total_answers += 1

                        elif q.local_code in ("evidence", "info"):
                            Answer.objects.update_or_create(
                                submission=sub,
                                question=q,
                                defaults={
                                    "value": {"type": "text", "value": "Registro de evidências (seed)."},
                                    "evidence": "Evidências complementares.",
                                },
                            )
                            total_answers += 1

                # Recalcular progresso
                sub.recalc_progress(commit=True)

        self.stdout.write(
            self.style.SUCCESS(
                f"OK! Submissions e respostas geradas. Total de respostas criadas/atualizadas: {total_answers}."
            )
        )

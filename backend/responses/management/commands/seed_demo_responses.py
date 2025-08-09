from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal
import random

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

        # cria submissions por cliente e por template
        total_answers = 0
        for cli in clientes:
            for template in (t_nist, t_infra):
                sub, created = Submission.objects.get_or_create(
                    customer=cli,
                    template=template,
                    framework=template.framework,  # coerente
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

                # perguntas deste template
                # (perguntas = todas dos controles do template)
                qset = (
                    Question.objects.filter(control__in=template.controls.all())
                    .select_related("control")
                    .order_by("control__domain__order", "control__order", "order", "id")
                )

                # preenche algumas respostas (não todas, para simular progresso)
                # 60% das questões respondidas
                questions = list(qset)
                random.shuffle(questions)
                target = int(len(questions) * 0.6)

                for q in questions[:target]:
                    # NIST: primeira pergunta é scale 1..5 (local_code="score")
                    # Infra: primeira pergunta é choice yes/partial/no/na (local_code="status")
                    # dentro do for q in questions[:target]:
                    if template.slug == "nist-csf-2-pt-maturidade":
                        if q.local_code in ("policy", "practice"):
                            val = random.randint(1, 5)
                            Answer.objects.update_or_create(
                                submission=sub,
                                question=q,
                                defaults={
                                    "value": {"type": "scale", "value": val},
                                    "score": Decimal(str(val)),
                                    "evidence": f"Auto-seed {q.local_code} nível {val}.",
                                },
                            )
                            total_answers += 1

                        elif q.local_code == "info":
                            Answer.objects.update_or_create(
                                submission=sub,
                                question=q,
                                defaults={
                                    "value": {
                                        "type": "text",
                                        "value": "Notas e links (seed).",
                                    },
                                    "evidence": "Informações complementares cadastradas pelo seed.",
                                },
                            )
                            total_answers += 1

                        elif q.local_code == "attachment":
                            # você pode só registrar metadado; upload real via API de answers com multipart
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

                        elif q.local_code == "evidence" or q.local_code == "info":
                            Answer.objects.update_or_create(
                                submission=sub,
                                question=q,
                                defaults={
                                    "value": {
                                        "type": "text",
                                        "value": "Registro de evidências (seed).",
                                    },
                                    "evidence": "Evidências complementares.",
                                },
                            )
                            total_answers += 1

                    elif template.slug == "infraestrutura-basico":
                        if q.local_code == "status":
                            choice_pool = ["yes", "partial", "no", "na"]
                            pick = random.choice(choice_pool)

                            # score baseado no weight (se existir)
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
                        elif q.local_code == "evidence":
                            Answer.objects.update_or_create(
                                submission=sub,
                                question=q,
                                defaults={
                                    "value": {"type": "text", "value": ""},
                                    "evidence": "Registro de evidências (seed).",
                                },
                            )
                            total_answers += 1

                # recalcula progresso ao final
                sub.recalc_progress(commit=True)

        self.stdout.write(
            self.style.SUCCESS(
                f"OK! Submissions e respostas geradas. Total de respostas criadas/atualizadas: {total_answers}."
            )
        )

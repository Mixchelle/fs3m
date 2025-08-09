from django.core.management.base import BaseCommand
from assessments.models import AssessmentType, FrameworkAssessmentConfig
from frameworks.models import Framework

class Command(BaseCommand):
    help = "Cria AssessmentType e FrameworkAssessmentConfig padrão para NIST."

    def handle(self, *args, **options):
        at, _ = AssessmentType.objects.get_or_create(
            slug="maturity-1-5",
            defaults={"name":"Maturidade 1–5", "description":"Escala 1–5 baseada em 'score'."}
        )
        fw = Framework.objects.get(slug="nist-csf-2-pt")  # criado no seu seed
        FrameworkAssessmentConfig.objects.update_or_create(
            framework=fw, assessment_type=at,
            defaults={"mapping":{"score_code":"score","goal":3.0}, "is_default": True}
        )
        self.stdout.write(self.style.SUCCESS("OK: assessment type + config NIST criados."))

from django.db import transaction
from assessments.engine import REGISTRY
from assessments.models import Assessment, AssessmentType, FrameworkAssessmentConfig
# ajuste import do Submission conforme seu app
from responses.models import Submission

def run_assessment(submission_id: int, assessment_type_slug: str | None = None):
    submission = Submission.objects.select_related("framework").get(id=submission_id)
    framework = submission.framework

    # descobrir tipo
    fw_cfg = None
    at = None
    if assessment_type_slug:
        at = AssessmentType.objects.get(slug=assessment_type_slug)
        fw_cfg = FrameworkAssessmentConfig.objects.get(framework=framework, assessment_type=at)
    else:
        fw_cfg = FrameworkAssessmentConfig.objects.filter(framework=framework, is_default=True).select_related("assessment_type").first()
        if not fw_cfg:
            raise ValueError("Nenhuma avaliação padrão configurada para este framework.")
        at = fw_cfg.assessment_type

    calc = REGISTRY.get(at.slug)
    if not calc:
        raise ValueError(f"Não há calculadora registrada para '{at.slug}'.")

    with transaction.atomic():
        assessment, _ = Assessment.objects.update_or_create(
            submission=submission,
            defaults={"assessment_type": at, "framework": framework}
        )
        return calc(assessment, fw_cfg)

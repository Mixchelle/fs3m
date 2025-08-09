from django.db import models
from django.utils.translation import gettext_lazy as _
from frameworks.models import Framework
# ajuste estes imports para o seu app real de submissões/respostas
from responses.models import Submission  # ou 'submissions' se seu app chamar diferente

class AssessmentType(models.Model):
    slug = models.SlugField(unique=True)           # ex.: 'maturity-1-5'
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    config = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

class FrameworkAssessmentConfig(models.Model):
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE)
    assessment_type = models.ForeignKey(AssessmentType, on_delete=models.CASCADE)
    mapping = models.JSONField(default=dict, blank=True)  # ex.: {"score_code":"score","goal":3.0}
    is_default = models.BooleanField(default=True)

    class Meta:
        unique_together = ("framework", "assessment_type")

    def __str__(self):
        return f"{self.framework.slug} -> {self.assessment_type.slug}"

class Assessment(models.Model):
    submission = models.OneToOneField(
        Submission, on_delete=models.CASCADE, related_name="assessment"
    )
    assessment_type = models.ForeignKey(AssessmentType, on_delete=models.PROTECT)
    framework = models.ForeignKey(Framework, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    summary = models.JSONField(default=dict, blank=True)  # médias gerais, status, etc.

    def __str__(self):
        return f"{self.assessment_type.slug} - sub#{self.submission_id}"

class AssessmentBucket(models.Model):
    class Level(models.TextChoices):
        FUNCTION = "FUNCTION", _("Function")   # ex.: GV
        CATEGORY = "CATEGORY", _("Category")   # ex.: GV.OC
        CONTROL  = "CONTROL",  _("Control")    # ex.: GV.OC-01

    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="buckets"
    )
    level = models.CharField(max_length=10, choices=Level.choices)
    code = models.CharField(max_length=32)     # 'GV', 'GV.OC', 'GV.OC-01'
    name = models.CharField(max_length=200, blank=True)
    metrics = models.JSONField(default=dict, blank=True)  # {media, objetivo, status...}
    order = models.IntegerField(default=0)

    class Meta:
        index_together = [("assessment", "level", "code")]
        unique_together = ("assessment", "level", "code")

    def __str__(self):
        return f"{self.assessment_id} {self.level}:{self.code}"

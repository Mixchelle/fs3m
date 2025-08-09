# responses/models.py
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone

from users.models import CustomUser
from frameworks.models import Framework, FormTemplate, Question

try:
    # Postgres only
    from django.contrib.postgres.fields import ArrayField
    HAS_ARRAY = True
except Exception:
    HAS_ARRAY = False


class Submission(models.Model):
    """
    Uma 'resposta de formulário' para um Template específico por um cliente.
    Usa Template (que referencia Framework) para descobrir quantas questões existem,
    calcular progresso, etc.
    """
    STATUS_CHOICES = [
        ("draft", "Rascunho"),
        ("in_review", "Em análise"),
        ("pending", "Pendente"),
        ("submitted", "Concluído"),
        ("archived", "Arquivado"),
    ]

    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="submissions")
    template = models.ForeignKey(FormTemplate, on_delete=models.PROTECT, related_name="submissions")
    framework = models.ForeignKey(Framework, on_delete=models.PROTECT, related_name="submissions")

    assigned_to = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_submissions"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    version = models.PositiveIntegerField(default=1)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("customer", "template", "version")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.template.name} - {self.customer.email} (v{self.version})"

    @property
    def total_questions(self) -> int:
        # total de perguntas do template
        return Question.objects.filter(
            control__in=self.template.controls.all()
        ).count()

    @property
    def answered_count(self) -> int:
        return self.answers.count()

    def recalc_progress(self, commit=True):
        total = self.total_questions or 1
        self.progress = round(100 * (self.answered_count / total), 2)
        if commit:
            self.save(update_fields=["progress", "updated_at"])

    def mark_submitted(self):
        self.status = "submitted"
        self.finished_at = timezone.now()
        self.save(update_fields=["status", "finished_at", "updated_at"])


class Answer(models.Model):
    """
    Resposta flexível por questão.
    - `value` guarda qualquer tipo (número, texto, choices, multi) em JSON.
    - `score` pode ser usado para normalizar pontuação (ex.: 1..5).
    - `evidence` campo opcional (pode receber texto e/ou links). Se quiser criptografar,
      use `encrypted_evidence` + helpers get/set (abaixo).
    """
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")

    # valor genérico (ex.: {"type":"scale","value":3} ou {"type":"text","value":"..."} etc.)
    value = models.JSONField(default=dict, blank=True)

    # evidências/observações livres
    evidence = models.TextField(blank=True, null=True)

    # se preferir criptografar evidências, use este campo binário:
    encrypted_evidence = models.BinaryField(blank=True, null=True, editable=False)

    # pontuação normalizada opcional
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # escolhas múltiplas (apenas se Postgres; opcional)
    if HAS_ARRAY:
        multichoice = ArrayField(models.CharField(max_length=128), null=True, blank=True)
    else:
        multichoice = models.JSONField(default=list, blank=True)  # fallback

    attachment = models.FileField(upload_to="answers/", null=True, blank=True)

    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("submission", "question")
        ordering = ["question_id"]

    def __str__(self):
        return f"Answer(submission={self.submission_id}, q={self.question_id})"

    # ===== helpers de criptografia simples (opcionais) =====
    def set_encrypted_evidence(self, text: str):
        """
        Criptografa e grava em encrypted_evidence (usa a primeira chave em settings.FERNET_KEYS).
        Mantém `evidence` limpo/None quando usar criptografia.
        """
        from cryptography.fernet import Fernet

        keys = getattr(settings, "FERNET_KEYS", [])
        if not keys:
            # sem chave => armazena como texto simples
            self.evidence = text
            self.encrypted_evidence = None
            return

        f = Fernet(keys[0].encode())
        token = f.encrypt((text or "").encode())
        self.encrypted_evidence = token
        self.evidence = None

    def get_decrypted_evidence(self) -> str:
        from cryptography.fernet import Fernet, InvalidToken

        if not self.encrypted_evidence:
            return self.evidence or ""

        keys = getattr(settings, "FERNET_KEYS", [])
        for k in keys:
            try:
                f = Fernet(k.encode())
                return f.decrypt(self.encrypted_evidence).decode()
            except (InvalidToken, ValueError):
                continue
        return ""  # se nenhuma chave funcionar

    # recálculo de progresso do submission ao salvar/excluir
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.submission.recalc_progress(commit=True)

    def delete(self, *args, **kwargs):
        sid = self.submission
        super().delete(*args, **kwargs)
        sid.recalc_progress(commit=True)

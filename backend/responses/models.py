# responses/models.py
from django.db import models
from django.db.models import UniqueConstraint
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
    Usa o Template (que referencia o Framework) para descobrir quantas questões existem,
    calcular progresso e controlar o fluxo de status.
    """
    STATUS_CHOICES = [
        ("draft", "Rascunho"),
        ("in_review", "Em análise"),   # cliente envia para análise
        ("pending", "Pendente"),       # opcional: analista pediu ajustes
        ("submitted", "Concluído"),    # analista finalizou a análise
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
    finished_at = models.DateTimeField(null=True, blank=True)   # quando o cliente envia para análise
    approved = models.BooleanField(default=False)                # uso livre (ex.: análise aprovada)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # mantém unicidade por template+versão
        unique_together = ("customer", "template", "version")
        ordering = ["-updated_at"]
        # garante **apenas 1 submission por framework** por cliente
        constraints = [
            UniqueConstraint(fields=["customer", "framework"], name="uniq_submission_per_customer_framework"),
        ]

    def __str__(self):
        return f"{self.template.name} - {self.customer.email} (v{self.version})"

    # ======= Métricas e progresso =======

    @property
    def total_questions(self) -> int:
        # total de perguntas do template
        return Question.objects.filter(control__in=self.template.controls.all()).count()

    @property
    def answered_count(self) -> int:
        return self.answers.count()

    def recalc_progress(self, commit: bool = True):
        total = self.total_questions or 1
        self.progress = round(100 * (self.answered_count / total), 2)
        if commit:
            self.save(update_fields=["progress", "updated_at"])

    # ======= Completude =======

    def required_questions_qs(self):
        """Perguntas obrigatórias do template."""
        return Question.objects.filter(control__in=self.template.controls.all(), required=True)

    def all_questions_qs(self):
        """Todas as perguntas do template."""
        return Question.objects.filter(control__in=self.template.controls.all())

    def unanswered_question_ids(self):
        """
        IDs de perguntas que ainda não têm Answer.
        Regra: se houver 'required', exigimos todas as 'required';
               se não houver nenhuma 'required', exigimos TODAS.
        """
        required = self.required_questions_qs()
        base_qs = required if required.exists() else self.all_questions_qs()
        answered_qids = set(self.answers.values_list("question_id", flat=True))
        return list(base_qs.exclude(id__in=answered_qids).values_list("id", flat=True))

    def is_complete(self) -> bool:
        return len(self.unanswered_question_ids()) == 0

    @property
    def is_editable(self) -> bool:
        """Formulário só é editável em rascunho ou pendente."""
        return self.status in ("draft", "pending")

    # ======= Fluxo / transições =======

    ALLOWED_TRANSITIONS = {
        "draft": {"pending", "in_review"},
        "pending": {"in_review", "draft"},
        "in_review": {"submitted", "pending"},
        "submitted": set(),
        "archived": set(),
    }

    def transition(self, new_status: str):
        if new_status not in dict(self.STATUS_CHOICES):
            raise ValueError("Status inválido.")
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(f"Transição inválida: {self.status} -> {new_status}")
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])

    # ======= Ações de caso de uso =======

    def send_for_review(self, enforce_complete: bool = True):
        """
        Ação do CLIENTE ao finalizar preenchimento:
          - se 'enforce_complete' True, exige formulário completo;
          - muda para 'in_review' e registra 'finished_at'.
        """
        if enforce_complete and not self.is_complete():
            missing = self.unanswered_question_ids()
            raise ValueError(f"Formulário incompleto. Faltam {len(missing)} perguntas.")

        self.status = "in_review"
        self.finished_at = timezone.now()
        self.save(update_fields=["status", "finished_at", "updated_at"])

    def finish_review(self, approve: bool | None = None):
        """
        Ação do ANALISTA ao concluir a análise:
          - muda para 'submitted'
          - opcionalmente marca 'approved'/'approved_at'
        """
        self.status = "submitted"
        updates = ["status", "updated_at"]

        if approve is not None:
            self.approved = bool(approve)
            self.approved_at = timezone.now()
            updates += ["approved", "approved_at"]

        self.save(update_fields=updates)

    # Mantido por compatibilidade (se algo no código ainda chamar)
    def mark_submitted(self):
        """
        Compat: usar send_for_review() para cliente e finish_review() para analista.
        Aqui, interpretamos como 'cliente concluiu' -> vai para análise.
        """
        self.send_for_review(enforce_complete=True)


class Answer(models.Model):
    """
    Resposta flexível por questão.
    - `value` guarda qualquer tipo (número, texto, choices, multi) em JSON.
    - `score` pode ser usado para normalizar pontuação (ex.: 1..5).
    - `evidence` campo opcional (pode receber texto e/ou links). Se quiser criptografar,
      use `encrypted_evidence` + helpers get/set.
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
        super().save(*args, **kwargs)
        # Sempre recalcula (criação e atualização) para refletir progresso corretamente.
        self.submission.recalc_progress(commit=True)

    def delete(self, *args, **kwargs):
        submission = self.submission
        super().delete(*args, **kwargs)
        submission.recalc_progress(commit=True)

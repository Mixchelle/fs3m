# users/models_audit.py
from django.db import models
from django.conf import settings

class UserAuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create"
        UPDATE = "update"
        ACTIVATE = "activate"
        DEACTIVATE = "deactivate"
        LOGIN = "login"
        LOGOUT = "logout"
        ENABLE_2FA = "enable_2fa"
        DISABLE_2FA = "disable_2fa"
        GENERATE_REPORT = "generate_report"
        VIEW_REPORT = "view_report"
        DELETE_REPORT = "delete_report"
        PASSWORD_CHANGE = "password_change"
        PASSWORD_RESET = "password_reset"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="audit_actions"
    )  # quem fez
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="audit_targets"
    )  # em quem foi feito (quando aplicável)
    action = models.CharField(max_length=32, choices=Action.choices)
    metadata = models.JSONField(default=dict, blank=True)  # detalhes extras (ids de relatório, antes/depois, etc.)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["target_user", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} by {self.actor_id} -> {self.target_user_id} @ {self.created_at:%Y-%m-%d %H:%M:%S}"

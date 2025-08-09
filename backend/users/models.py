from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
import secrets

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O campo 'email' é obrigatório")
        email = self.normalize_email(email)
        if not extra_fields.get("username"):
            extra_fields["username"] = self._generate_unique_username(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "gestor")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário precisa ter is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa ter is_superuser=True.")
        return self.create_user(email, password, **extra_fields)

    def _generate_unique_username(self, email):
        base = email.split("@")[0]
        username = base
        i = 1
        while self.model.objects.filter(username=username).exists():
            username = f"{base}_{i}"
            i += 1
        return username


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("cliente", "Cliente"),
        ("subcliente", "Subcliente"),
        ("analista", "Analista"),
        ("gestor", "Gestor"),
    ]

    # --- Campos base ---
    username = models.CharField(max_length=150, unique=True, blank=True)
    nome = models.CharField(max_length=255, verbose_name="Nome Completo")
    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="cliente")

    # --- M2M explícitos (não conflitar com defaults do AbstractUser) ---
    groups = models.ManyToManyField(Group, related_name="customuser_groups", blank=True)
    user_permissions = models.ManyToManyField(
        Permission, related_name="customuser_permissions", blank=True
    )

    # --- Regras de negócio ---
    # Subcliente -> cliente pai (quando role='subcliente')
    cliente = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subclientes",
        limit_choices_to={"role": "cliente"},
        verbose_name="Cliente Associado (para Subcliente)",
    )

    # Analista -> (opcional) gestor responsável (futuras equipes)
    gestor_referente = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analistas",
        limit_choices_to={"role": "gestor"},
        verbose_name="Gestor Referente (para Analista)",
    )

    # Cliente -> IDs de formulários permitidos (futuro: obrigatório)
    formularios_ids = ArrayField(
        base_field=models.IntegerField(),
        default=list,
        blank=True,
        verbose_name="IDs de Formulários Permitidos (Cliente)",
        help_text="Lista de IDs de formulários que este cliente pode acessar.",
    )

    # --- 2FA (TOTP) ---
    is_2fa_enabled = models.BooleanField(default=False, verbose_name="2FA habilitado")
    otp_secret = models.CharField(max_length=64, blank=True, default="", verbose_name="Segredo TOTP")
    otp_backup_codes = ArrayField(
        base_field=models.CharField(max_length=32),
        default=list,
        blank=True,
        null=True,
        verbose_name="Códigos de backup 2FA",
        help_text="Códigos de uso único para recuperação (opcional).",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nome"]

    objects = CustomUserManager()

    # Helpers 2FA
    def ensure_otp_secret(self) -> None:
        """Gera e salva um segredo TOTP se estiver vazio."""
        if not self.otp_secret:
            # 20 bytes em hex maiúsculo é simples e compatível com pyotp
            self.otp_secret = secrets.token_hex(20).upper()

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = CustomUser.objects._generate_unique_username(self.email)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} ({self.email})"

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["nome"]
        permissions = [
            ("view_report", "Pode ver relatórios de segurança"),
            ("create_report", "Pode criar relatórios de segurança"),
            ("delete_report", "Pode excluir relatórios de segurança"),
        ]

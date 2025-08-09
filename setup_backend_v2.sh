#!/usr/bin/env bash
set -e

# ==== CONFIG BÁSICA ====
PROJECT_DIR="backend_v2"
DJANGO_PROJECT="config"
USER_APP="users"
PYTHON_BIN="python3"            # ajuste se for pyenv/conda
DJANGO_VERSION="5.0.*"

echo "🚀 Criando estrutura em: $PROJECT_DIR"
rm -rf "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# ==== VENV & DEPENDÊNCIAS ====
$PYTHON_BIN -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel

# Django + DRF + utilitários de produção
pip install \
  "Django==$DJANGO_VERSION" \
  djangorestframework \
  drf-spectacular drf-spectacular-sidecar \
  django-cors-headers \
  django-environ \
  django-filter \
  psycopg2-binary \
  gunicorn \
  sentry-sdk

# ==== PROJETO DJANGO ====
django-admin startproject "$DJANGO_PROJECT" .
python manage.py startapp "$USER_APP"

# ==== SETTINGS (sobrescreve) ====
cat > $DJANGO_PROJECT/settings.py << 'PY'
import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, "dev-secret"),
    ALLOWED_HOSTS=(list, ["*"]),
    DB_URL=(str, "sqlite:///db.sqlite3"),
)

# .env (opcional)
if (BASE_DIR / ".env").exists():
    environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 3rd
    "rest_framework",
    "drf_spectacular",
    "corsheaders",

    # apps
    "users",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db("DB_URL")  # ex: postgres://user:pass@localhost:5432/fs3m
}

AUTH_USER_MODEL = "users.CustomUser"

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

CORS_ALLOW_ALL_ORIGINS = True  # ajuste depois para os domínios do Next

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "FS3M API v2",
    "DESCRIPTION": "Backend reestruturado, começando por users.",
    "VERSION": "2.0.0",
}
PY

# ==== URLs (sobrescreve) ====
cat > $DJANGO_PROJECT/urls.py << 'PY'
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    # Apps
    path("api/users/", include("users.urls")),
]
PY

# ==== APP USERS: models ====
cat > $USER_APP/models.py << 'PY'
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O campo 'email' é obrigatório")
        email = self.normalize_email(email)
        # username auto, se não vier
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
        ("funcionario", "Funcionário"),
        ("gestor", "Gestor"),
    ]
    # Campos
    username = models.CharField(max_length=150, unique=True, blank=True)
    nome = models.CharField(max_length=255, verbose_name="Nome Completo")
    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="cliente")

    # Relacionamentos explícitos pra não conflitar com AbstractUser defaults
    groups = models.ManyToManyField(Group, related_name="customuser_groups", blank=True)
    user_permissions = models.ManyToManyField(
        Permission, related_name="customuser_permissions", blank=True
    )

    cliente = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subclientes",
        limit_choices_to={"role": "cliente"},
        verbose_name="Cliente Associado",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nome"]  # username vira auto

    objects = CustomUserManager()

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
PY

# ==== APP USERS: admin ====
cat > $USER_APP/admin.py << 'PY'
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("id", "nome", "email", "role", "is_active", "is_staff")
    search_fields = ("email", "nome", "username")
    ordering = ("nome",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("nome", "role", "cliente")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "nome", "role", "password1", "password2", "is_staff", "is_superuser")}
        ),
    )
    readonly_fields = ("last_login", "date_joined")
PY

# ==== APP USERS: urls/views/serializers mínimos ====
mkdir -p $USER_APP
cat > $USER_APP/urls.py << 'PY'
from django.urls import path
from .views import MeView

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
]
PY

cat > $USER_APP/serializers.py << 'PY'
from rest_framework import serializers
from .models import CustomUser

class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "email", "nome", "role"]
PY

cat > $USER_APP/views.py << 'PY'
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import MeSerializer

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(MeSerializer(request.user).data)
PY

# ==== MIGRATIONS & RUN ====
python manage.py makemigrations
python manage.py migrate

echo
echo "🧑‍💻 Criando superuser (email: admin@example.com, senha: admin123) ..."
python - << 'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from users.models import CustomUser
if not CustomUser.objects.filter(email="admin@example.com").exists():
    CustomUser.objects.create_superuser(
        email="admin@example.com", password="admin123", nome="Admin"
    )
    print("✅ Superuser criado.")
else:
    print("ℹ️  Superuser já existe.")
PY

echo
echo "✅ Pronto! Ative o venv e rode:"
echo "   cd $PROJECT_DIR"
echo "   source .venv/bin/activate"
echo "   python manage.py runserver 0.0.0.0:8000"
echo
echo "Docs: http://localhost:8000/api/docs/  |  Schema: /api/schema/"

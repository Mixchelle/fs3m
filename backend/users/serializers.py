# users/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


# =======================
# AUTH (LOGIN + 2FA)
# =======================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Permite login por email OU username.
    Se 2FA estiver habilitado (is_2fa_enabled), exige otp_code (TOTP ou backup).
    """
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    otp_code = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        email = attrs.get("email")
        username = attrs.get("username")
        password = attrs.get("password")
        otp_code = (attrs.get("otp_code") or "").strip()

        if not (email or username):
            raise serializers.ValidationError({"detail": "Informe 'email' ou 'username'."})
        if not password:
            raise serializers.ValidationError({"password": "O campo password é obrigatório."})

        # Busca usuário (email case-insensitive)
        if email:
            user = User.objects.filter(email__iexact=email).first()
        else:
            user = User.objects.filter(username=username).first()

        if not user:
            raise serializers.ValidationError({"detail": "Usuário não encontrado."})
        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Senha incorreta."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "Usuário inativo."})

        # 2FA (TOTP + backup)
        if getattr(user, "is_2fa_enabled", False):
            import pyotp
            valid = False
            if getattr(user, "otp_secret", ""):
                totp = pyotp.TOTP(user.otp_secret)
                valid = totp.verify(otp_code, valid_window=1)
            if not valid and getattr(user, "otp_backup_codes", None):
                if otp_code and otp_code in user.otp_backup_codes:
                    valid = True
                    # consome o backup code usado
                    user.otp_backup_codes = [c for c in user.otp_backup_codes if c != otp_code]
                    user.save(update_fields=["otp_backup_codes"])
            if not valid:
                raise serializers.ValidationError({"detail": "OTP requerido/ inválido.", "mfa_required": True})

        # Garante o USERNAME_FIELD correto (no seu model é 'email')
        attrs[self.username_field] = getattr(user, self.username_field)
        data = super().validate(attrs)

        data["user"] = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "nome": getattr(user, "nome", user.get_full_name()),
            "role": getattr(user, "role", ""),
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active,
            "is_2fa_enabled": getattr(user, "is_2fa_enabled", False),
        }
        return data


# =======================
# USERS (CRUD)
# =======================
class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "username", "nome", "role",
            "is_active", "is_staff", "is_superuser", "date_joined",
            "cliente", "gestor_referente", "formularios_ids",
            "is_2fa_enabled",
        ]
        read_only_fields = ["id", "username", "is_staff", "is_superuser", "date_joined"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = [
            "id", "email", "nome", "role", "password",
            "cliente", "gestor_referente", "formularios_ids",
            "is_2fa_enabled",  # permitir já criar com 2FA habilitado (secret pode ser gerado depois)
        ]

    def validate_email(self, value: str):
        # unicidade case-insensitive
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Já existe um usuário com este email.")
        return value

    def validate(self, attrs):
        role = attrs.get("role")
        cliente = attrs.get("cliente")
        gestor = attrs.get("gestor_referente")

        # Regras de negócio
        if role == "subcliente":
            if not cliente:
                raise serializers.ValidationError({"cliente": "Subcliente requer um cliente associado."})
            if getattr(cliente, "role", None) != "cliente":
                raise serializers.ValidationError({"cliente": "O cliente associado deve ter role='cliente'."})

        if role == "cliente":
            if cliente is not None:
                raise serializers.ValidationError({"cliente": "Cliente não deve referenciar outro cliente."})

        if role == "analista":
            # gestor_referente é opcional, mas se vier deve ser 'gestor'
            if gestor and getattr(gestor, "role", None) != "gestor":
                raise serializers.ValidationError({"gestor_referente": "Deve referenciar um usuário com role='gestor'."})

        return attrs

    def create(self, validated_data):
        pwd = validated_data.pop("password")
        # use o manager para respeitar regras (gera username único, etc.)
        user = User.objects.create_user(password=pwd, **validated_data)
        # se is_2fa_enabled True e não tiver secret, gera um
        if getattr(user, "is_2fa_enabled", False):
            user.ensure_otp_secret()
            user.save(update_fields=["otp_secret"])
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, required=False)

    class Meta:
        model = User
        fields = [
            "email", "nome", "role", "is_active", "password",
            "cliente", "gestor_referente", "formularios_ids",
            "is_2fa_enabled",
        ]

    def validate_email(self, value: str):
        # unicidade case-insensitive (excluindo o próprio)
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Já existe um usuário com este email.")
        return value

    def validate(self, attrs):
        role = attrs.get("role", getattr(self.instance, "role", None))
        cliente = attrs.get("cliente", getattr(self.instance, "cliente", None))
        gestor = attrs.get("gestor_referente", getattr(self.instance, "gestor_referente", None))

        if role == "subcliente":
            if not cliente:
                raise serializers.ValidationError({"cliente": "Subcliente requer um cliente associado."})
            if getattr(cliente, "role", None) != "cliente":
                raise serializers.ValidationError({"cliente": "O cliente associado deve ter role='cliente'."})

        if role == "cliente":
            if cliente is not None:
                raise serializers.ValidationError({"cliente": "Cliente não deve referenciar outro cliente."})

        if role == "analista":
            if gestor and getattr(gestor, "role", None) != "gestor":
                raise serializers.ValidationError({"gestor_referente": "Deve referenciar um usuário com role='gestor'."})

        return attrs

    def update(self, instance, validated_data):
        pwd = validated_data.pop("password", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)

        if pwd:
            instance.set_password(pwd)

        # Se habilitar 2FA e não houver secret ainda, gera
        if getattr(instance, "is_2fa_enabled", False) and not getattr(instance, "otp_secret", ""):
            instance.ensure_otp_secret()

        instance.save()
        return instance

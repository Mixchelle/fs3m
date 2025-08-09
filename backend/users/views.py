# users/views.py
from django.contrib.auth import get_user_model
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserListSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)
from .models_audit import UserAuditLog
from .utils import request_fingerprint

User = get_user_model()


# ========= PERMISSIONS =========
class IsAdminOrSelf(permissions.BasePermission):
    """
    Permite acesso ao próprio recurso ou a admins.
    Use via get_permissions() por action.
    """
    def has_object_permission(self, request, view, obj):
        return bool(request.user and (request.user.is_staff or obj.id == request.user.id))


# ========= VIEWSET (CRUD de usuários) =========
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("nome")

    # Ativar/Inativar usuário (apenas admin)
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def set_active(self, request, pk=None):
        user = self.get_object()
        new_state = bool(request.data.get("is_active"))
        old_state = user.is_active

        if old_state != new_state:
            user.is_active = new_state
            user.save(update_fields=["is_active"])

            ip, ua = request_fingerprint(request)
            UserAuditLog.objects.create(
                actor=request.user,
                target_user=user,
                action=UserAuditLog.Action.ACTIVATE if new_state else UserAuditLog.Action.DEACTIVATE,
                metadata={"from": old_state, "to": new_state},
                ip=ip,
                user_agent=ua,
            )

        return Response({"id": user.id, "is_active": user.is_active}, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserListSerializer

    def get_permissions(self):
        # list/create/destroy: apenas admin
        if self.action in ["list", "create", "destroy"]:
            return [permissions.IsAdminUser()]
        # retrieve/update/partial_update: admin OU o próprio usuário
        if self.action in ["retrieve", "update", "partial_update"]:
            return [permissions.IsAuthenticated(), IsAdminOrSelf()]
        # default: autenticado
        return [permissions.IsAuthenticated()]

    # Checa permissão por-objeto
    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        return super().partial_update(request, *args, **kwargs)


# ========= AUTH VIEWS =========
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    /api/auth/token/ -> login (email/username + 2FA via otp_code)
    """
    serializer_class = CustomTokenObtainPairSerializer

    # Se quiser logar IP/UA no serializer (ex.: para UserAuditLog),
    # passamos o request no contexto.
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class LogoutAndBlacklistRefreshTokenForUserView(APIView):
    """
    /api/auth/logout/ -> POST {"refresh": "<token>"}
    Coloca o refresh em blacklist. Requer 'rest_framework_simplejwt.token_blacklist' no INSTALLED_APPS.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "Campo 'refresh' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except Exception:
            return Response({"detail": "Refresh token inválido."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    """
    /api/auth/me/ -> GET dados do usuário logado | PATCH atualização parcial
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserListSerializer(request.user).data)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

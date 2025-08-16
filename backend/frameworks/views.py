from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    Framework,
    Domain,
    Control,
    Question,
    ChoiceOption,
    ScoringModel,
    FormTemplate,
    TemplateItem,
    ControlMapping,
)
from .serializers import (
    FrameworkWriteSerializer,
    FrameworkReadSerializer,
    FrameworkDetailSerializer,
    DomainWriteSerializer,
    DomainReadSerializer,
    ControlWriteSerializer,
    ControlReadSerializer,
    QuestionWriteSerializer,
    QuestionReadSerializer,
    ChoiceOptionSerializer,
    ScoringModelSerializer,
    FormTemplateWriteSerializer,
    FormTemplateReadSerializer,
    TemplateItemWriteSerializer,
    TemplateItemReadSerializer,
    ControlMappingSerializer,
)

# Reutilizável em manual_parameters quando quiser exibir explicitamente o header
AUTH_HEADER = openapi.Parameter(
    name="Authorization",
    in_=openapi.IN_HEADER,
    description="JWT: Bearer <token>",
    type=openapi.TYPE_STRING,
    required=False,
)

# ========================= Frameworks =========================

class FrameworkViewSet(viewsets.ModelViewSet):
    """
    CRUD de Frameworks de maturidade.
    """
    queryset = Framework.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return FrameworkDetailSerializer if self.action == "retrieve" else FrameworkReadSerializer
        return FrameworkWriteSerializer

    @swagger_auto_schema(
        operation_summary="Listar frameworks",
        operation_description="Retorna a lista paginada de frameworks.",
        manual_parameters=[AUTH_HEADER],
        responses={200: FrameworkReadSerializer(many=True)},
        tags=["Frameworks"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Detalhar framework",
        operation_description="Retorna um framework com domínios e controles aninhados.",
        manual_parameters=[AUTH_HEADER],
        responses={200: FrameworkDetailSerializer, 404: "Não encontrado"},
        tags=["Frameworks"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar framework",
        operation_description="Cria um novo framework.",
        manual_parameters=[AUTH_HEADER],
        request_body=FrameworkWriteSerializer,
        responses={201: FrameworkReadSerializer, 400: "Dados inválidos"},
        tags=["Frameworks"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar framework",
        operation_description="Atualiza todos os campos do framework.",
        manual_parameters=[AUTH_HEADER],
        request_body=FrameworkWriteSerializer,
        responses={200: FrameworkReadSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Frameworks"],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar parcialmente framework",
        operation_description="Atualiza parcialmente campos do framework.",
        manual_parameters=[AUTH_HEADER],
        request_body=FrameworkWriteSerializer,
        responses={200: FrameworkReadSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Frameworks"],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir framework",
        operation_description="Remove um framework.",
        manual_parameters=[AUTH_HEADER],
        responses={204: "Deletado", 404: "Não encontrado"},
        tags=["Frameworks"],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# ========================= Domínios =========================

class DomainViewSet(viewsets.ModelViewSet):
    """
    CRUD de Domínios pertencentes a um framework.
    """
    queryset = Domain.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return DomainReadSerializer if self.action in ["list", "retrieve"] else DomainWriteSerializer

    @swagger_auto_schema(
        operation_summary="Listar domínios",
        operation_description="Retorna a lista de domínios (paginada).",
        manual_parameters=[AUTH_HEADER],
        responses={200: DomainReadSerializer(many=True)},
        tags=["Domínios"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Detalhar domínio",
        operation_description="Retorna um domínio com controles e filhos.",
        manual_parameters=[AUTH_HEADER],
        responses={200: DomainReadSerializer, 404: "Não encontrado"},
        tags=["Domínios"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar domínio",
        manual_parameters=[AUTH_HEADER],
        request_body=DomainWriteSerializer,
        responses={201: DomainReadSerializer, 400: "Dados inválidos"},
        tags=["Domínios"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar domínio",
        manual_parameters=[AUTH_HEADER],
        request_body=DomainWriteSerializer,
        responses={200: DomainReadSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Domínios"],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar parcialmente domínio",
        manual_parameters=[AUTH_HEADER],
        request_body=DomainWriteSerializer,
        responses={200: DomainReadSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Domínios"],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir domínio",
        manual_parameters=[AUTH_HEADER],
        responses={204: "Deletado", 404: "Não encontrado"},
        tags=["Domínios"],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# ========================= Controles =========================

class ControlViewSet(viewsets.ModelViewSet):
    """
    CRUD de Controles (ligados a domínio e framework).
    """
    queryset = Control.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return ControlReadSerializer if self.action in ["list", "retrieve"] else ControlWriteSerializer

    @swagger_auto_schema(
        operation_summary="Listar controles",
        manual_parameters=[AUTH_HEADER],
        responses={200: ControlReadSerializer(many=True)},
        tags=["Controles"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Detalhar controle",
        manual_parameters=[AUTH_HEADER],
        responses={200: ControlReadSerializer, 404: "Não encontrado"},
        tags=["Controles"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar controle",
        manual_parameters=[AUTH_HEADER],
        request_body=ControlWriteSerializer,
        responses={201: ControlReadSerializer, 400: "Dados inválidos"},
        tags=["Controles"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar controle",
        manual_parameters=[AUTH_HEADER],
        request_body=ControlWriteSerializer,
        responses={200: ControlReadSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Controles"],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar parcialmente controle",
        manual_parameters=[AUTH_HEADER],
        request_body=ControlWriteSerializer,
        responses={200: ControlReadSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Controles"],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir controle",
        manual_parameters=[AUTH_HEADER],
        responses={204: "Deletado", 404: "Não encontrado"},
        tags=["Controles"],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# ========================= Questões =========================

class QuestionViewSet(viewsets.ModelViewSet):
    """
    CRUD de Questões (opções vêm aninhadas no read).
    """
    queryset = Question.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return QuestionReadSerializer if self.action in ["list", "retrieve"] else QuestionWriteSerializer

    @swagger_auto_schema(
        operation_summary="Listar questões",
        manual_parameters=[AUTH_HEADER],
        responses={200: QuestionReadSerializer(many=True)},
        tags=["Questões"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Detalhar questão",
        manual_parameters=[AUTH_HEADER],
        responses={200: QuestionReadSerializer, 404: "Não encontrado"},
        tags=["Questões"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar questão",
        manual_parameters=[AUTH_HEADER],
        request_body=QuestionWriteSerializer,
        responses={201: QuestionReadSerializer, 400: "Dados inválidos"},
        tags=["Questões"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar questão",
        manual_parameters=[AUTH_HEADER],
        request_body=QuestionWriteSerializer,
        responses={200: QuestionReadSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Questões"],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar parcialmente questão",
        manual_parameters=[AUTH_HEADER],
        request_body=QuestionWriteSerializer,
        responses={200: QuestionReadSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Questões"],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir questão",
        manual_parameters=[AUTH_HEADER],
        responses={204: "Deletado", 404: "Não encontrado"},
        tags=["Questões"],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# ========================= Opções de Resposta =========================

class ChoiceOptionViewSet(viewsets.ModelViewSet):
    """
    CRUD de opções de resposta.
    """
    queryset = ChoiceOption.objects.all()
    serializer_class = ChoiceOptionSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Listar opções",
        manual_parameters=[AUTH_HEADER],
        responses={200: ChoiceOptionSerializer(many=True)},
        tags=["Opções"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Detalhar opção",
        manual_parameters=[AUTH_HEADER],
        responses={200: ChoiceOptionSerializer, 404: "Não encontrado"},
        tags=["Opções"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar opção",
        manual_parameters=[AUTH_HEADER],
        request_body=ChoiceOptionSerializer,
        responses={201: ChoiceOptionSerializer, 400: "Dados inválidos"},
        tags=["Opções"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar opção",
        manual_parameters=[AUTH_HEADER],
        request_body=ChoiceOptionSerializer,
        responses={200: ChoiceOptionSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Opções"],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar parcialmente opção",
        manual_parameters=[AUTH_HEADER],
        request_body=ChoiceOptionSerializer,
        responses={200: ChoiceOptionSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Opções"],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir opção",
        manual_parameters=[AUTH_HEADER],
        responses={204: "Deletado", 404: "Não encontrado"},
        tags=["Opções"],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# ========================= Modelos de Pontuação =========================

class ScoringModelViewSet(viewsets.ModelViewSet):
    """
    CRUD de modelos de pontuação (mapping/rules).
    """
    queryset = ScoringModel.objects.all()
    serializer_class = ScoringModelSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Listar modelos de pontuação",
        manual_parameters=[AUTH_HEADER],
        responses={200: ScoringModelSerializer(many=True)},
        tags=["Pontuação"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Detalhar modelo de pontuação",
        manual_parameters=[AUTH_HEADER],
        responses={200: ScoringModelSerializer, 404: "Não encontrado"},
        tags=["Pontuação"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar modelo de pontuação",
        manual_parameters=[AUTH_HEADER],
        request_body=ScoringModelSerializer,
        responses={201: ScoringModelSerializer, 400: "Dados inválidos"},
        tags=["Pontuação"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar modelo de pontuação",
        manual_parameters=[AUTH_HEADER],
        request_body=ScoringModelSerializer,
        responses={200: ScoringModelSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Pontuação"],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar parcialmente modelo de pontuação",
        manual_parameters=[AUTH_HEADER],
        request_body=ScoringModelSerializer,
        responses={200: ScoringModelSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Pontuação"],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir modelo de pontuação",
        manual_parameters=[AUTH_HEADER],
        responses={204: "Deletado", 404: "Não encontrado"},
        tags=["Pontuação"],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# ========================= Templates de Formulário =========================

class FormTemplateViewSet(viewsets.ModelViewSet):
    """
    CRUD de templates de formulário (com itens).
    """
    queryset = FormTemplate.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return FormTemplateReadSerializer if self.action in ["list", "retrieve"] else FormTemplateWriteSerializer

    @swagger_auto_schema(
        operation_summary="Listar templates",
        manual_parameters=[AUTH_HEADER],
        responses={200: FormTemplateReadSerializer(many=True)},
        tags=["Templates"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Detalhar template",
        manual_parameters=[AUTH_HEADER],
        responses={200: FormTemplateReadSerializer, 404: "Não encontrado"},
        tags=["Templates"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar template",
        manual_parameters=[AUTH_HEADER],
        request_body=FormTemplateWriteSerializer,
        responses={201: FormTemplateReadSerializer, 400: "Dados inválidos"},
        tags=["Templates"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar template",
        manual_parameters=[AUTH_HEADER],
        request_body=FormTemplateWriteSerializer,
        responses={200: FormTemplateReadSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Templates"],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar parcialmente template",
        manual_parameters=[AUTH_HEADER],
        request_body=FormTemplateWriteSerializer,
        responses={200: FormTemplateReadSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Templates"],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir template",
        manual_parameters=[AUTH_HEADER],
        responses={204: "Deletado", 404: "Não encontrado"},
        tags=["Templates"],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# ========================= Itens do Template =========================

class TemplateItemViewSet(viewsets.ModelViewSet):
    """
    CRUD de itens do template (liga formulário a controle/questão).
    """
    queryset = TemplateItem.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return TemplateItemReadSerializer if self.action in ["list", "retrieve"] else TemplateItemWriteSerializer

    @swagger_auto_schema(
        operation_summary="Listar itens de template",
        manual_parameters=[AUTH_HEADER],
        responses={200: TemplateItemReadSerializer(many=True)},
        tags=["Template Items"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Detalhar item de template",
        manual_parameters=[AUTH_HEADER],
        responses={200: TemplateItemReadSerializer, 404: "Não encontrado"},
        tags=["Template Items"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar item de template",
        manual_parameters=[AUTH_HEADER],
        request_body=TemplateItemWriteSerializer,
        responses={201: TemplateItemReadSerializer, 400: "Dados inválidos"},
        tags=["Template Items"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar item de template",
        manual_parameters=[AUTH_HEADER],
        request_body=TemplateItemWriteSerializer,
        responses={200: TemplateItemReadSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Template Items"],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar parcialmente item de template",
        manual_parameters=[AUTH_HEADER],
        request_body=TemplateItemWriteSerializer,
        responses={200: TemplateItemReadSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Template Items"],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir item de template",
        manual_parameters=[AUTH_HEADER],
        responses={204: "Deletado", 404: "Não encontrado"},
        tags=["Template Items"],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# ========================= Mapeamento de Controles =========================

class ControlMappingViewSet(viewsets.ModelViewSet):
    """
    CRUD de mapeamentos entre controles (origin -> target).
    """
    queryset = ControlMapping.objects.all()
    serializer_class = ControlMappingSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Listar mapeamentos de controle",
        manual_parameters=[AUTH_HEADER],
        responses={200: ControlMappingSerializer(many=True)},
        tags=["Mapeamentos"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Detalhar mapeamento de controle",
        manual_parameters=[AUTH_HEADER],
        responses={200: ControlMappingSerializer, 404: "Não encontrado"},
        tags=["Mapeamentos"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Criar mapeamento de controle",
        manual_parameters=[AUTH_HEADER],
        request_body=ControlMappingSerializer,
        responses={201: ControlMappingSerializer, 400: "Dados inválidos"},
        tags=["Mapeamentos"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar mapeamento de controle",
        manual_parameters=[AUTH_HEADER],
        request_body=ControlMappingSerializer,
        responses={200: ControlMappingSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Mapeamentos"],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Atualizar parcialmente mapeamento de controle",
        manual_parameters=[AUTH_HEADER],
        request_body=ControlMappingSerializer,
        responses={200: ControlMappingSerializer, 400: "Dados inválidos", 404: "Não encontrado"},
        tags=["Mapeamentos"],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Excluir mapeamento de controle",
        manual_parameters=[AUTH_HEADER],
        responses={204: "Deletado", 404: "Não encontrado"},
        tags=["Mapeamentos"],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

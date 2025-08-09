from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
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


class FrameworkViewSet(viewsets.ModelViewSet):
    queryset = Framework.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            if self.action == "retrieve":
                return FrameworkDetailSerializer
            return FrameworkReadSerializer
        return FrameworkWriteSerializer


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return DomainReadSerializer
        return DomainWriteSerializer


class ControlViewSet(viewsets.ModelViewSet):
    queryset = Control.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ControlReadSerializer
        return ControlWriteSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return QuestionReadSerializer
        return QuestionWriteSerializer


class ChoiceOptionViewSet(viewsets.ModelViewSet):
    queryset = ChoiceOption.objects.all()
    serializer_class = ChoiceOptionSerializer
    permission_classes = [IsAuthenticated]


class ScoringModelViewSet(viewsets.ModelViewSet):
    queryset = ScoringModel.objects.all()
    serializer_class = ScoringModelSerializer
    permission_classes = [IsAuthenticated]


class FormTemplateViewSet(viewsets.ModelViewSet):
    queryset = FormTemplate.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return FormTemplateReadSerializer
        return FormTemplateWriteSerializer


class TemplateItemViewSet(viewsets.ModelViewSet):
    queryset = TemplateItem.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return TemplateItemReadSerializer
        return TemplateItemWriteSerializer


class ControlMappingViewSet(viewsets.ModelViewSet):
    queryset = ControlMapping.objects.all()
    serializer_class = ControlMappingSerializer
    permission_classes = [IsAuthenticated]

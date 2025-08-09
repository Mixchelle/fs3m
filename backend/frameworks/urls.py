from rest_framework.routers import DefaultRouter
from .views import (
    FrameworkViewSet,
    DomainViewSet,
    ControlViewSet,
    QuestionViewSet,
    ChoiceOptionViewSet,
    ScoringModelViewSet,
    FormTemplateViewSet,
    TemplateItemViewSet,
    ControlMappingViewSet,
)

router = DefaultRouter()
router.register(r"frameworks", FrameworkViewSet)
router.register(r"domains", DomainViewSet)
router.register(r"controls", ControlViewSet)
router.register(r"questions", QuestionViewSet)
router.register(r"options", ChoiceOptionViewSet)
router.register(r"scoring-models", ScoringModelViewSet)
router.register(r"templates", FormTemplateViewSet)
router.register(r"template-items", TemplateItemViewSet)
router.register(r"control-mappings", ControlMappingViewSet)

urlpatterns = router.urls

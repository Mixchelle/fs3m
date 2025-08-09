from rest_framework.routers import DefaultRouter
from .views import SubmissionViewSet, AnswerViewSet

router = DefaultRouter()
router.register(r"submissions", SubmissionViewSet, basename="submission")
router.register(r"answers", AnswerViewSet, basename="answer")

urlpatterns = router.urls

# responses/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import SubmissionViewSet, AnswerViewSet, ClientDashboardView

router = DefaultRouter()
router.register(r"submissions", SubmissionViewSet, basename="submission")
router.register(r"answers", AnswerViewSet, basename="answer")

urlpatterns = [
    path("dashboard/<int:client_id>/", ClientDashboardView.as_view(), name="client-dashboard"),
]
urlpatterns += router.urls

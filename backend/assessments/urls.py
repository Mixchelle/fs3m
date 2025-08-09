from django.urls import path
from assessments.views import RunAssessmentView

urlpatterns = [
    path("assessments/run/<int:submission_id>/", RunAssessmentView.as_view(), name="run-assessment"),
]

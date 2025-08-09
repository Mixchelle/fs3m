from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Submission, Answer
from .serializers import (
    SubmissionCreateSerializer, SubmissionReadSerializer,
    AnswerWriteSerializer, AnswerReadSerializer,
)

class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.select_related("template", "framework", "customer", "assigned_to")
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["customer", "framework", "template", "status"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return SubmissionReadSerializer
        return SubmissionCreateSerializer

    @action(methods=["post"], detail=True, url_path="submit")
    def mark_submitted(self, request, pk=None):
        submission: Submission = self.get_object()
        submission.mark_submitted()
        return Response(SubmissionReadSerializer(submission).data)

    @action(methods=["get"], detail=True, url_path="answers")
    def list_answers(self, request, pk=None):
        qs = Answer.objects.filter(submission_id=pk).select_related("question")
        return Response(AnswerReadSerializer(qs, many=True).data)

    @action(methods=["post"], detail=True, url_path="recalc")
    def recalc(self, request, pk=None):
        sub = self.get_object()
        sub.recalc_progress(commit=True)
        return Response(SubmissionReadSerializer(sub).data)


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.select_related("submission", "question")
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["submission", "submission__customer", "submission__framework"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AnswerReadSerializer
        return AnswerWriteSerializer

    @action(methods=["post"], detail=False, url_path="upsert")
    def upsert(self, request):
        """
        Autosave: envia {submission, question, value, evidence_plain?, encrypt_evidence?}
        """
        ser = AnswerWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = ser.save()
        return Response(AnswerReadSerializer(obj).data, status=status.HTTP_201_CREATED)

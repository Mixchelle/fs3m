# responses/views.py
from rest_framework import viewsets, status as drf_status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.timezone import now

from .models import Submission, Answer
from .serializers import (
    SubmissionCreateSerializer, SubmissionReadSerializer,
    AnswerWriteSerializer, AnswerReadSerializer, SubmissionBriefSerializer
)
from .utils import get_or_create_client_submission

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
        sub = self.get_object()
        sub.mark_submitted()
        return Response(SubmissionReadSerializer(sub).data)

    @action(methods=["post"], detail=True, url_path="start-review")
    def start_review(self, request, pk=None):
        sub = self.get_object()
        sub.status = "in_review"
        sub.save(update_fields=["status", "updated_at"])
        return Response(SubmissionReadSerializer(sub).data)

    @action(methods=["post"], detail=True, url_path="set-pending")
    def set_pending(self, request, pk=None):
        sub = self.get_object()
        sub.status = "pending"
        sub.save(update_fields=["status", "updated_at"])
        return Response(SubmissionReadSerializer(sub).data)

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
        ser = AnswerWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = ser.save()
        return Response(AnswerReadSerializer(obj).data, status=drf_status.HTTP_201_CREATED)


class ClientDashboardView(APIView):
    """
    GET /api/responses/dashboard/<client_id>/?ensure=1&template=nist-csf-2-0

    - se ensure=1 e o cliente não tiver submissão, cria uma do template informado (ou NIST por padrão)
    - retorna a submissão mais recente (brief) para o card do front
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id: int):
        ensure = request.query_params.get("ensure") in ("1", "true", "yes")
        template_slug = request.query_params.get("template")  # opcional

        sub = (
            Submission.objects
            .filter(customer_id=client_id)
            .order_by("-updated_at", "-created_at")
            .first()
        )
        if not sub and ensure:
            sub = get_or_create_client_submission(client_id, template_slug)

        return Response({
            "client_id": client_id,
            "submission": SubmissionBriefSerializer(sub).data if sub else None,
            "retrieved_at": now().isoformat(),
        })

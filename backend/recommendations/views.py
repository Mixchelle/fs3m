from decimal import Decimal
from collections import defaultdict
import logging
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Recomendacao
from .serializers import RecomendacaoSerializer
from responses.models import Submission, Answer

logger = logging.getLogger(__name__)

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def verificar_recomendacoes_faltantes(request, submission_id):
    """
    NIST: qualquer controle com política/prática/score < 3 precisa ter recomendação.
    Verifica o Submission e lista as perguntas/controles faltantes (sem recomendação).
    """
    submission = get_object_or_404(Submission, id=submission_id)

    # carrega respostas do submission
    answers = (
        Answer.objects
        .filter(submission=submission)
        .select_related("question__control__domain")
    )

    # agrupa por controle (código NIST) e coleta valores
    # Também pegamos a perguntaId (usaremos question.id como string)
    per_control = defaultdict(lambda: {"policy": [], "practice": [], "score": [], "qids": set(), "domain_title": "", "func_code": ""})

    for a in answers:
        q = a.question
        ctl = q.control
        dom = ctl.domain
        code = ctl.code  # "DE.AE-02"
        rec = per_control[code]
        rec["domain_title"] = dom.title
        rec["func_code"] = dom.code.split(".")[0] if dom.code else ""
        local = (q.local_code or "").strip().lower()

        # normaliza valor numérico (score se houver)
        val = None
        if a.score is not None:
            try:
                val = Decimal(str(a.score))
            except Exception:
                val = None
        if val is None:
            v = a.value or {}
            if isinstance(v, dict) and "value" in v:
                try:
                    val = Decimal(str(v["value"]))
                except Exception:
                    val = None

        if local in ("politica", "policy"):
            if val is not None:
                rec["policy"].append(val)
        elif local in ("pratica", "practice"):
            if val is not None:
                rec["practice"].append(val)
        elif local == "score":
            if val is not None:
                rec["score"].append(val)

        rec["qids"].add(str(q.id))

    # controles com nota < 3
    below = []
    for ctl_code, data in per_control.items():
        # regra: se existir política/prática, usa média delas; senão usa score
        policy = (sum(data["policy"]) / len(data["policy"])) if data["policy"] else None
        practice = (sum(data["practice"]) / len(data["practice"])) if data["practice"] else None
        score = (sum(data["score"]) / len(data["score"])) if data["score"] else None

        if policy is not None or practice is not None:
            parts = [v for v in (policy, practice) if v is not None]
            media = sum(parts) / len(parts) if parts else None
        else:
            media = score

        if media is not None and media < Decimal("3"):
            below.append((ctl_code, data))

    # recomendações existentes por perguntaId (ou por nist code)
    existentes_qids = set(
        Recomendacao.objects.filter(submission=submission)
        .values_list("perguntaId", flat=True)
    )
    existentes_nist = set(
        Recomendacao.objects.filter(submission=submission)
        .values_list("nist", flat=True)
    )

    faltantes = []
    for ctl_code, data in below:
        # se não houver nenhuma recomendação ligada por perguntaId OU pelo code NIST, consideramos faltante
        if data["qids"].isdisjoint(existentes_qids) and (ctl_code not in existentes_nist):
            faltantes.append({
                "nist": ctl_code,
                "domain": data["domain_title"],
                "perguntaIds": list(data["qids"]),
            })

    resp = {
        "total_faltantes": len(faltantes),
        "faltantes": faltantes,
        "pode_enviar": len(faltantes) == 0,
    }
    return Response(resp, status=status.HTTP_200_OK)

class RecomendacaoListCreateView(generics.ListCreateAPIView):
    serializer_class = RecomendacaoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Recomendacao.objects.filter(
            cliente_id=self.kwargs["cliente_id"],
            submission_id=self.kwargs["submission_id"]
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({
            "cliente_id": self.kwargs["cliente_id"],
            "submission_id": self.kwargs["submission_id"],
            "request": self.request,
        })
        return ctx

class RecomendacaoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RecomendacaoSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Recomendacao.objects.all()

    def perform_update(self, serializer):
        if "analista" in serializer.validated_data:
            serializer.validated_data.pop("analista")
        serializer.save()

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import PlanoDeAcao, PlanoDeAcaoRecomendacao
from .serializers import PlanoDeAcaoSerializer

class PlanoDeAcaoListCreateView(generics.ListCreateAPIView):
    serializer_class = PlanoDeAcaoSerializer

    def get_queryset(self):
        submission_id = self.request.query_params.get("submission_id")
        qs = PlanoDeAcao.objects
        if submission_id:
            qs = qs.filter(submission_id=submission_id)
        return qs

    def post(self, request, *args, **kwargs):
        user = request.user
        dados = request.data.copy()
        submission_id = dados.get("submission_id")

        if getattr(user, "role", None) in ["funcionario", "gestor"]:
            existente = PlanoDeAcao.objects.filter(criado_por=user, submission_id=submission_id).first()
            if existente:
                serializer = self.get_serializer(existente, data=dados, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=dados)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class AtualizarKanbanView(APIView):
    def post(self, request):
        dados = request.data.get("dados", [])
        for item in dados:
            try:
                rel = PlanoDeAcaoRecomendacao.objects.get(
                    plano_id=item["plano_id"], recomendacao_id=item["recomendacao_id"]
                )
                rel.status = item["status"]
                rel.ordem = item["ordem"]
                rel.data_alteracao = timezone.now()
                rel.save()
            except PlanoDeAcaoRecomendacao.DoesNotExist:
                continue
        return Response({"detail": "Kanban atualizado com sucesso!"}, status=status.HTTP_200_OK)

from django.urls import path
from .views import (
    RecomendacaoListCreateView,
    RecomendacaoRetrieveUpdateDestroyView,
    verificar_recomendacoes_faltantes,
)

urlpatterns = [
    path("recommendations/<int:cliente_id>/<int:submission_id>/", RecomendacaoListCreateView.as_view(), name="recomendacoes-list-create"),
    path("recommendations/<int:pk>/", RecomendacaoRetrieveUpdateDestroyView.as_view(), name="recomendacao-detail"),
    path("submissions/<int:submission_id>/recommendations/check-missing/", verificar_recomendacoes_faltantes, name="verificar-recomendacoes"),
]

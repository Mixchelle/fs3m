from django.urls import path
from .views import AtualizarKanbanView, PlanoDeAcaoListCreateView

urlpatterns = [
    path("", PlanoDeAcaoListCreateView.as_view(), name="planodeacao-list-create"),
    path("kanban/update/", AtualizarKanbanView.as_view(), name="kanban-update"),
]

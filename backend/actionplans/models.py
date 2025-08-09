from django.db import models
from django.utils import timezone
from users.models import CustomUser
from recommendations.models import Recomendacao

class PlanoDeAcao(models.Model):
    cliente = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="planos_cliente")
    criado_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="planos_criados")
    observacoes = models.TextField(default="Nenhuma observação")
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    prazo = models.CharField(max_length=255, blank=True, default="")
    gravidade = models.CharField(max_length=255, blank=True, default="")
    urgencia = models.CharField(max_length=255, blank=True, default="")
    categoria = models.CharField(max_length=255, blank=True, default="")
    orcamentoMax = models.CharField(max_length=255, blank=True, default="")
    submission_id = models.IntegerField(null=True, blank=True)  # ← substitui formularioRespondidoId
    recomendacoes = models.ManyToManyField(Recomendacao, through="PlanoDeAcaoRecomendacao")

    def __str__(self):
        return f"Plano {self.id} - Cliente: {self.cliente}"

class PlanoDeAcaoRecomendacao(models.Model):
    STATUS_CHOICES = [("A Fazer","A Fazer"),("Em Progresso","Em Progresso"),("Finalizado","Finalizado")]
    plano = models.ForeignKey(PlanoDeAcao, on_delete=models.CASCADE)
    recomendacao = models.ForeignKey(Recomendacao, on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="A Fazer")
    data_alteracao = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["ordem"]

from django.db import models
from django.core.exceptions import ValidationError
from users.models import CustomUser
from responses.models import Submission  # ← usa seu app atual

class Recomendacao(models.Model):
    CATEGORIA_CHOICES = [
        ("Governar (GV)", "Governar (GV)"),
        ("Identificar (ID)", "Identificar (ID)"),
        ("Proteger (PR)", "Proteger (PR)"),
        ("Detectar (DE)", "Detectar (DE)"),
        ("Responder (RS)", "Responder (RS)"),
        ("Recuperar (RC)", "Recuperar (RC)"),
    ]
    PRIORIDADE_CHOICES = [("baixa", "Baixa"), ("media", "Média"), ("alta", "Alta")]
    URGENCIA_CHOICES = [("1","Muito Baixo"),("2","Baixo"),("3","Moderado"),("4","Alto"),("5","Muito Alto")]
    GRAVIDADE_CHOICES = [("1","Muito Baixa"),("2","Baixa"),("3","Moderada"),("4","Alta"),("5","Muito Alta")]
    APLICABILIDADE_CHOICES = [("Política","Política"),("Prática","Prática"),("Ambas","Ambas")]

    # Relacionamentos
    cliente = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="recomendacoes_cliente")
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="recomendacoes_submission")
    analista = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="recomendacoes_analista")

    # Campos principais
    nome = models.CharField(max_length=255)
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES)
    aplicabilidade = models.CharField(max_length=20, choices=APLICABILIDADE_CHOICES, default="Ambas",
                                      help_text="Indica se a recomendação se aplica a Política, Prática ou Ambas.")
    tecnologia = models.CharField(max_length=255, default="Agnóstico")
    nist = models.CharField(max_length=50)  # ex.: "DE.AE-02"
    prioridade = models.CharField(max_length=50, choices=PRIORIDADE_CHOICES)
    responsavel = models.CharField(max_length=255, default="Não definido")

    # Datas e prazos
    data_inicio = models.DateField()
    data_fim = models.DateField()
    meses = models.PositiveIntegerField()

    # Detalhes
    detalhes = models.TextField()
    investimentos = models.CharField(max_length=255)
    riscos = models.TextField(default="Não informado")
    justificativa = models.TextField(default="Não informado")
    observacoes = models.TextField(default="Nenhuma observação adicional")

    # Avaliação
    urgencia = models.CharField(max_length=1, choices=URGENCIA_CHOICES)
    gravidade = models.CharField(max_length=1, choices=GRAVIDADE_CHOICES)

    # Status
    cumprida = models.BooleanField(default=False)
    data_cumprimento = models.DateField(null=True, blank=True)
    comprovante = models.FileField(upload_to="comprovantes/", null=True, blank=True)

    # Metadata
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    # Referência da pergunta/controle (string)
    # Sugestão: guardar o ID da Question ou o local_code; aqui deixamos livre
    perguntaId = models.CharField(max_length=50, default="Não informado", blank=True, db_column="perguntaId")

    class Meta:
        verbose_name = "Recomendação"
        verbose_name_plural = "Recomendações"
        ordering = ["-prioridade", "data_fim"]

    def __str__(self):
        return f"{self.nome} (Cliente: {self.cliente})"

    def clean(self):
        if self.data_inicio and self.data_fim and self.data_inicio > self.data_fim:
            raise ValidationError("A data de início deve ser anterior à data de término.")
        if not self.meses or self.meses <= 0:
            raise ValidationError("O prazo em meses deve ser maior que zero.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

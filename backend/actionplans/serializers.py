from rest_framework import serializers
from .models import PlanoDeAcao, PlanoDeAcaoRecomendacao
from recommendations.models import Recomendacao
from recommendations.serializers import RecomendacaoSerializer
from users.models import CustomUser

class UsuarioSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "nome", "email", "role")

class PlanoDeAcaoSerializer(serializers.ModelSerializer):
    cliente = UsuarioSimplesSerializer(read_only=True)
    criado_por = UsuarioSimplesSerializer(read_only=True)
    recomendacoes_ordem = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    recomendacoes = serializers.SerializerMethodField(read_only=True)

    prazo = serializers.CharField(allow_blank=True, required=False)
    gravidade = serializers.CharField(allow_blank=True, required=False)
    urgencia = serializers.CharField(allow_blank=True, required=False)
    categoria = serializers.CharField(allow_blank=True, required=False)
    orcamentoMax = serializers.CharField(allow_blank=True, required=False)
    submission_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = PlanoDeAcao
        fields = [
            "id","cliente","criado_por","observacoes","data_criacao","data_atualizacao",
            "recomendacoes_ordem","recomendacoes","prazo","gravidade","urgencia",
            "categoria","orcamentoMax","submission_id",
        ]
        read_only_fields = ["id","cliente","criado_por","data_criacao","data_atualizacao","recomendacoes"]

    def get_recomendacoes(self, obj):
        vinculos = PlanoDeAcaoRecomendacao.objects.filter(plano=obj).order_by("ordem")
        out = []
        for v in vinculos:
            rec = RecomendacaoSerializer(v.recomendacao).data
            rec["ordem"] = v.ordem
            rec["status"] = v.status
            rec["data_alteracao"] = v.data_alteracao
            out.append(rec)
        return out

    def create(self, validated_data):
        rec_ids = validated_data.pop("recomendacoes_ordem", [])
        user = self.context["request"].user
        plano = PlanoDeAcao.objects.create(
            cliente=user,
            criado_por=user,
            observacoes=validated_data.get("observacoes", "Nenhuma observação"),
            prazo=validated_data.get("prazo", ""),
            gravidade=validated_data.get("gravidade", ""),
            urgencia=validated_data.get("urgencia", ""),
            categoria=validated_data.get("categoria", ""),
            orcamentoMax=validated_data.get("orcamentoMax", ""),
            submission_id=validated_data.get("submission_id"),
        )
        for ordem, rec_id in enumerate(rec_ids):
            PlanoDeAcaoRecomendacao.objects.create(plano=plano, recomendacao_id=rec_id, ordem=ordem)
        return plano

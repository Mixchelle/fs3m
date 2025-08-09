from rest_framework import serializers
from .models import Recomendacao
from django.shortcuts import get_object_or_404
from users.models import CustomUser
from responses.models import Submission

class RecomendacaoSerializer(serializers.ModelSerializer):
    cliente = serializers.PrimaryKeyRelatedField(read_only=True)
    submission = serializers.PrimaryKeyRelatedField(read_only=True)
    analista = serializers.PrimaryKeyRelatedField(read_only=True)

    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)
    urgencia_display = serializers.CharField(source='get_urgencia_display', read_only=True)
    gravidade_display = serializers.CharField(source='get_gravidade_display', read_only=True)

    class Meta:
        model = Recomendacao
        fields = '__all__'
        read_only_fields = ['id', 'criado_em', 'atualizado_em', 'analista']

    def create(self, validated_data):
        request = self.context.get('request')
        cliente_id = self.context.get('cliente_id')
        submission_id = self.context.get('submission_id')

        cliente = get_object_or_404(CustomUser, id=cliente_id)
        submission = get_object_or_404(Submission, id=submission_id, customer_id=cliente_id)

        return Recomendacao.objects.create(
            cliente=cliente,
            submission=submission,
            analista=request.user,
            **validated_data
        )

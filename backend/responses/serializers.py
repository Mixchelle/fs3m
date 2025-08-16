# responses/serializers.py
from rest_framework import serializers
from .models import Submission, Answer
from frameworks.models import Question, FormTemplate


class SubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ["id", "customer", "template", "framework", "status", "version", "assigned_to"]
        read_only_fields = ["id", "framework"]

    def validate(self, data):
        template: FormTemplate = data["template"]
        customer = data["customer"]
        framework = template.framework

        # força coerência
        data["framework"] = framework

        # 🔒 garante 1 por framework (exceto se você quiser permitir múltiplos "arquivados")
        exists = Submission.objects.filter(customer=customer, framework=framework).exists()
        if exists:
            raise serializers.ValidationError(
                {"non_field_errors": [f"Este cliente já possui uma submission para o framework '{framework.slug}'."]}
            )
        return data

class SubmissionReadSerializer(serializers.ModelSerializer):
    total_questions = serializers.IntegerField(read_only=True)
    answered_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id", "customer", "template", "framework", "status", "version",
            "progress", "total_questions", "answered_count",
            "assigned_to", "created_at", "updated_at", "finished_at", "approved", "approved_at",
        ]
        read_only_fields = fields


class AnswerWriteSerializer(serializers.ModelSerializer):
    submission = serializers.PrimaryKeyRelatedField(queryset=Submission.objects.all())
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())

    # Para permitir enviar evidence criptografada em um campo separado
    evidence_plain = serializers.CharField(required=False, allow_blank=True, write_only=True)
    encrypt_evidence = serializers.BooleanField(required=False, default=False, write_only=True)

    class Meta:
        model = Answer
        fields = [
            "id", "submission", "question", "value", "score",
            "multichoice", "attachment", "evidence", "evidence_plain", "encrypt_evidence",
            "answered_at",
        ]
        read_only_fields = ["id", "answered_at"]

    def create(self, validated):
        # upsert-like (garante unicidade)
        evidence_plain = validated.pop("evidence_plain", None)
        encrypt = validated.pop("encrypt_evidence", False)

        obj, created = Answer.objects.update_or_create(
            submission=validated["submission"],
            question=validated["question"],
            defaults=validated,
        )
        if evidence_plain is not None:
            if encrypt:
                obj.set_encrypted_evidence(evidence_plain)
            else:
                obj.evidence = evidence_plain
                obj.encrypted_evidence = None
            obj.save(update_fields=["evidence", "encrypted_evidence", "answered_at"])
        return obj

    def update(self, instance, validated):
        evidence_plain = validated.pop("evidence_plain", None)
        encrypt = validated.pop("encrypt_evidence", False)

        for k, v in validated.items():
            setattr(instance, k, v)

        if evidence_plain is not None:
            if encrypt:
                instance.set_encrypted_evidence(evidence_plain)
            else:
                instance.evidence = evidence_plain
                instance.encrypted_evidence = None

        instance.save()
        return instance


class AnswerReadSerializer(serializers.ModelSerializer):
    evidence_decrypted = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = [
            "id", "submission", "question", "value", "score",
            "multichoice", "attachment", "evidence", "evidence_decrypted",
            "answered_at",
        ]

    def get_evidence_decrypted(self, obj: Answer):
        return obj.get_decrypted_evidence()



class SubmissionBriefSerializer(serializers.ModelSerializer):
    template = serializers.SerializerMethodField()
    framework = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "id", "status", "progress", "version", "created_at", "updated_at",
            "template", "framework",
        ]

    def get_template(self, obj):
        t: FormTemplate = obj.template
        return {"id": t.id, "name": t.name, "slug": t.slug, "version": t.version}

    def get_framework(self, obj):
        f: Framework = obj.template.framework
        return {"id": f.id, "slug": f.slug, "name": f.name, "version": f.version}
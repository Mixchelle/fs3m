from rest_framework import serializers
from .models import (
    Framework,
    Domain,
    Control,
    ScoringModel,
    Question,
    ChoiceOption,
    FormTemplate,
    TemplateItem,
    ControlMapping,
)


# ============ Small, reusable serializers ============

class ScoringModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoringModel
        fields = ["id", "name", "slug", "mapping", "rules"]


class ChoiceOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChoiceOption
        fields = ["id", "label", "value", "weight", "order", "active"]


# ============ Question serializers ============

class QuestionWriteSerializer(serializers.ModelSerializer):
    """
    Write serializer (create/update) for a question with its options.
    """
    options = ChoiceOptionSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = [
            "id",
            "control",
            "local_code",
            "prompt",
            "type",
            "required",
            "order",
            "meta",
            "scoring_model",
            "options",
        ]

    def create(self, validated_data):
        options_data = validated_data.pop("options", [])
        question = Question.objects.create(**validated_data)
        for idx, opt in enumerate(options_data):
            ChoiceOption.objects.create(question=question, order=idx, **opt)
        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop("options", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        # If options provided, replace all (simple & explicit).
        if options_data is not None:
            instance.options.all().delete()
            for idx, opt in enumerate(options_data):
                ChoiceOption.objects.create(question=instance, order=idx, **opt)
        return instance


class QuestionReadSerializer(serializers.ModelSerializer):
    options = ChoiceOptionSerializer(many=True, read_only=True)
    scoring_model = ScoringModelSerializer(read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "control",
            "local_code",
            "prompt",
            "type",
            "required",
            "order",
            "meta",
            "scoring_model",
            "options",
        ]


# ============ Control serializers ============

class ControlWriteSerializer(serializers.ModelSerializer):
    """
    Create/update control. Questions should be created via QuestionWriteSerializer endpoints.
    """
    class Meta:
        model = Control
        fields = [
            "id",
            "framework",
            "domain",
            "code",
            "title",
            "description",
            "order",
            "active",
            "scoring_model",
        ]


class ControlReadSerializer(serializers.ModelSerializer):
    domain = serializers.PrimaryKeyRelatedField(read_only=True)
    framework = serializers.PrimaryKeyRelatedField(read_only=True)
    scoring_model = ScoringModelSerializer(read_only=True)
    questions = QuestionReadSerializer(many=True, read_only=True)

    class Meta:
        model = Control
        fields = [
            "id",
            "framework",
            "domain",
            "code",
            "title",
            "description",
            "order",
            "active",
            "scoring_model",
            "questions",
        ]


# ============ Domain serializers ============

class DomainWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ["id", "framework", "code", "title", "parent", "order"]


class DomainReadSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    controls = ControlReadSerializer(many=True, read_only=True)

    class Meta:
        model = Domain
        fields = [
            "id",
            "framework",
            "code",
            "title",
            "parent",
            "order",
            "children",
            "controls",
        ]

    def get_children(self, obj):
        qs = obj.children.all().order_by("order", "id")
        return DomainReadSerializer(qs, many=True).data


# ============ Framework serializers ============

class FrameworkWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Framework
        fields = [
            "id",
            "slug",
            "name",
            "version",
            "description",
            "active",
            "editable",
        ]


class FrameworkReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Framework
        fields = [
            "id",
            "slug",
            "name",
            "version",
            "description",
            "active",
            "editable",
            "created_at",
            "updated_at",
        ]


class FrameworkDetailSerializer(FrameworkReadSerializer):
    domains = DomainReadSerializer(many=True, read_only=True)

    class Meta(FrameworkReadSerializer.Meta):
        fields = FrameworkReadSerializer.Meta.fields + ["domains"]


# ============ Template serializers ============

class TemplateItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateItem
        fields = ["id", "template", "control", "question", "order"]


class TemplateItemReadSerializer(serializers.ModelSerializer):
    control = ControlReadSerializer(read_only=True)
    question = QuestionReadSerializer(read_only=True)

    class Meta:
        model = TemplateItem
        fields = ["id", "template", "control", "question", "order"]


class FormTemplateWriteSerializer(serializers.ModelSerializer):
    """
    Allows optional bulk set of items (replace behavior).
    """
    items = TemplateItemWriteSerializer(many=True, required=False)

    class Meta:
        model = FormTemplate
        fields = [
            "id",
            "name",
            "slug",
            "framework",
            "version",
            "description",
            "active",
            "editable",
            "items",
        ]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        template = FormTemplate.objects.create(**validated_data)
        for idx, item in enumerate(items):
            TemplateItem.objects.create(
                template=template,
                control=item["control"],
                question=item.get("question"),
                order=item.get("order", idx),
            )
        return template

    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        if items is not None:
            instance.items.all().delete()
            for idx, item in enumerate(items):
                TemplateItem.objects.create(
                    template=instance,
                    control=item["control"],
                    question=item.get("question"),
                    order=item.get("order", idx),
                )
        return instance


class FormTemplateReadSerializer(serializers.ModelSerializer):
    framework = FrameworkReadSerializer(read_only=True)
    items = TemplateItemReadSerializer(many=True, read_only=True)

    class Meta:
        model = FormTemplate
        fields = [
            "id",
            "name",
            "slug",
            "framework",
            "version",
            "description",
            "active",
            "editable",
            "created_at",
            "updated_at",
            "items",
        ]


# ============ Cross mapping ============

class ControlMappingSerializer(serializers.ModelSerializer):
    origin = ControlReadSerializer(read_only=True)
    target = ControlReadSerializer(read_only=True)
    origin_id = serializers.PrimaryKeyRelatedField(
        queryset=Control.objects.all(), source="origin", write_only=True
    )
    target_id = serializers.PrimaryKeyRelatedField(
        queryset=Control.objects.all(), source="target", write_only=True
    )

    class Meta:
        model = ControlMapping
        fields = ["id", "origin", "target", "origin_id", "target_id", "weight", "note"]

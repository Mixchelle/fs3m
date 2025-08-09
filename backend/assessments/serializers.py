# assessments/serializers.py
from django.db.models import Case, When, IntegerField
from rest_framework import serializers
from assessments.models import Assessment, AssessmentBucket

class AssessmentBucketSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentBucket
        fields = ["level", "code", "name", "order", "metrics"]

class AssessmentSerializer(serializers.ModelSerializer):
    buckets = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = ["id", "framework", "assessment_type", "summary", "buckets"]
        depth = 1

    def get_buckets(self, obj):
        qs = obj.buckets.annotate(
            level_rank=Case(
                When(level="FUNCTION", then=0),
                When(level="CATEGORY", then=1),
                When(level="CONTROL", then=2),
                default=3,
                output_field=IntegerField(),
            )
        ).order_by("level_rank", "order", "code")
        return AssessmentBucketSerializer(qs, many=True).data

from rest_framework import serializers
from assessments.models import Assessment, AssessmentBucket, AssessmentType, FrameworkAssessmentConfig

class AssessmentBucketSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentBucket
        fields = ["level", "code", "name", "order", "metrics"]

class AssessmentSerializer(serializers.ModelSerializer):
    buckets = AssessmentBucketSerializer(many=True, read_only=True)

    class Meta:
        model = Assessment
        fields = ["id", "framework", "assessment_type", "summary", "buckets"]
        depth = 1

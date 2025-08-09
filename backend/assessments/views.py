from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from assessments.services import run_assessment
from assessments.serializers import AssessmentSerializer
# ajuste import Submission se quiser validar existência antes
from responses.models import Submission

# assessments/views.py
class RunAssessmentView(APIView):
    def post(self, request, submission_id):
        atype = request.query_params.get("type")  # 'maturity-1-5'
        only = request.query_params.get("only")   # ex.: 'function'
        try:
            assessment = run_assessment(submission_id, atype)
        except Submission.DoesNotExist:
            return Response({"error":"Submission não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        data = AssessmentSerializer(assessment).data
        if only == "function":
            data["buckets"] = [b for b in data["buckets"] if b["level"] == "FUNCTION"]
        return Response(data, status=status.HTTP_200_OK)

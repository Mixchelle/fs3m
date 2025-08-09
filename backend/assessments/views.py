from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from assessments.services import run_assessment
from assessments.serializers import AssessmentSerializer
# ajuste import Submission se quiser validar existência antes
from responses.models import Submission

class RunAssessmentView(APIView):
    def post(self, request, submission_id):
        atype = request.query_params.get("type")  # ex.: 'maturity-1-5'
        try:
            assessment = run_assessment(submission_id, atype)
        except Submission.DoesNotExist:
            return Response({"error":"Submission não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AssessmentSerializer(assessment).data, status=status.HTTP_200_OK)

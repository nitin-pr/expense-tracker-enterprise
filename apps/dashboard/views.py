from rest_framework.response import Response
from rest_framework.views import APIView

from .services import DashboardService


class DashboardSummaryView(APIView):
    def get(self, request):
        return Response(DashboardService().get_summary(request.user))

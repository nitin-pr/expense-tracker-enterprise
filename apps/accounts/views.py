from rest_framework.response import Response
from rest_framework.views import APIView


class WhoAmIView(APIView):
    """Minimal authenticated endpoint proving FirebaseAuthentication resolves a real user."""

    def get(self, request):
        return Response({
            "id": request.user.id,
            "email": request.user.email,
            "firebase_uid": request.user.firebase_uid,
        })

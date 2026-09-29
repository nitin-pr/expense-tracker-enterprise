from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotFoundError

from .permissions import IsCategoryOwner
from .repositories import CategoryRepository
from .serializers import CategorySerializer
from .services import CategoryService


def get_service():
    return CategoryService(repository=CategoryRepository())


class CategoryListCreateView(APIView):
    """List: defaults + this user's own. Create: always owned by request.user."""

    def get(self, request):
        categories = get_service().list_for_user(request.user)
        return Response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = get_service().create_category(
            user=request.user,
            name=serializer.validated_data["name"],
            icon=serializer.validated_data["icon"],
            color=serializer.validated_data["color"],
        )
        return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCategoryOwner]

    def get_object(self, pk, request):
        category = get_service().repository.get_by_id(pk)
        if category is None:
            raise NotFoundError(f"Category {pk} not found.")
        # Every category (default or any user's custom one) is visible via list,
        # so unlike Expense there's no existence-leakage concern here - a category
        # that exists but isn't yours correctly gets 403, not 404.
        self.check_object_permissions(request, category)
        return category

    def delete(self, request, pk):
        category = self.get_object(pk, request)
        get_service().delete_category(category)
        return Response(status=status.HTTP_204_NO_CONTENT)

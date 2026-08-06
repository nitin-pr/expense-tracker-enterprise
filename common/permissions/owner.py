from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """

    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the object
        return obj.user_id == request.user.id
from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    message="Only admin can access this endpoint"

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin
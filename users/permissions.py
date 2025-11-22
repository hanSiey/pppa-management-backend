from rest_framework import permissions

class IsAdminUserForCRUD(permissions.BasePermission):

    def has_permission(self, request, view):
        # Allow safe methods (GET, HEAD, OPTIONS) for any request (read access)
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # For write methods (POST, PUT, PATCH, DELETE), require staff/superuser status
        return request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
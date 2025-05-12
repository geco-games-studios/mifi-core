from rest_framework.permissions import BasePermission

class CanCreateClient(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.role in ['loan_officer', 'region_manager', 'manager', 'superuser']
        return True

class IsManagerOrHigher(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['manager', 'superuser']

class IsRegionManagerOrHigher(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['region_manager', 'manager', 'superuser']
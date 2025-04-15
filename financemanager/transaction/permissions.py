from rest_framework import permissions

class CategoryPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if request.method == 'POST' and request.data.get('is_system'):
            return request.user.is_superuser
        
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if obj.is_system:
            return request.user.is_superuser
        
        return obj.user == request.user
    
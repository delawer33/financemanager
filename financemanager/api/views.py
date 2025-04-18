from rest_framework import viewsets, permissions, generics
from rest_framework.permissions import AllowAny
from django.db.models import Q

from transaction.models import Transaction, Category
from transaction.permissions import CategoryPermission
from .serializers import (
    TransactionSerializer, 
    CategorySerializer,
    UserRegistrationSerializer
)


class TransactionViewset(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete']
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(user=user)


class CategoryViewset(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete']
    serializer_class = CategorySerializer
    permission_classes = [
        permissions.IsAuthenticated,
        CategoryPermission
    ]

    def get_queryset(self):
        return Category.objects.filter(
            Q(user=self.request.user) | Q(is_system=True)
            ).order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        return super().perform_create(serializer)


class RegisterViewAPI(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)



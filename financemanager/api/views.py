from rest_framework import viewsets, permissions, generics
from rest_framework.permissions import AllowAny

from transaction.models import Transaction, Category
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
        return Transaction.objects.filter(user=user).order_by('-id')

    class Meta:
        ordering = ['-id']


class CategoryViewset(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete']
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    # def get_queryset(self):
    #     user = self.request.user
    #     return Category.objects.filter(user=user).order_by('-id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        return super().perform_create(serializer)

    class Meta:
        ordering = ['-id']


class RegisterViewAPI(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)



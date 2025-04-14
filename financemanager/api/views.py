from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, generics
from rest_framework.permissions import AllowAny
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

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
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        cat = get_object_or_404(Category, id=kwargs.get('pk'))
        if cat.user != request.user:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    "message": "You are not allowed to delete system categories"
                }
            )
        return super().destroy(request, *args, **kwargs)

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



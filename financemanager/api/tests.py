from datetime import datetime
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from transaction.models import Transaction, Category
from authapp.models import Currency

User = get_user_model()

class CategoryAPITests(APITestCase):
    def setUp(self):
        self.currency = Currency.objects.create(
            name='USD',
            symbol='$'
        )

        self.user1 = User.objects.create_user(
            password='testpass1',
            email='testuser1@example.com',
            firstname='Test',
            lastname='User1',
            currency=self.currency
        )
        self.user2 = User.objects.create_user(
            password='testpass2',
            email='testuser2@example.com',
            firstname='Test',
            lastname='User2',
            currency=self.currency
        )
        
        self.token_user1 = RefreshToken.for_user(self.user1)
        self.token_user2 = RefreshToken.for_user(self.user2)
        
        self.category1 = Category.objects.create(
            name='Food',
            is_system=True
        )
        self.category2 = Category.objects.create(
            name='Transport',
            is_system=True
        )
        self.category_user1 = Category.objects.create(
            name='Food for dogs',
            user=self.user1
        )

        self.category_user2 = Category.objects.create(
            name='Food for cats',
            user=self.user1
        )
        self.transaction_with_system_category1 = Transaction.objects.create(
            amount=1000,
            date=datetime.now(),
            category=self.category1,
            user=self.user1
        )
        self.transaction_with_system_category2 = Transaction.objects.create(
            amount=1000,
            date=datetime.now(),
            category=self.category2,
            user=self.user1
        )
        self.transaction_with_user_category1 = Transaction.objects.create(
            amount=1000,
            date=datetime.now(),
            category=self.category_user1,
            user=self.user1
        )
        self.transaction_with_user_category2 = Transaction.objects.create(
            amount=1000,
            date=datetime.now(),
            category=self.category_user2,
            user=self.user1
        )

        self.category_list_url = reverse('api-categories-list')
        self.category1_detail_url = reverse('api-categories-detail', args=[self.category1.id])
        self.category2_detail_url = reverse('api-categories-detail', args=[self.category2.id])
        self.category_user1_detail_url = reverse('api-categories-detail', args=[self.category_user1.id])
        self.category_user2_detail_url = reverse('api-categories-detail', args=[self.category_user2.id])

    def authenticate_user1(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_user1.access_token}')
        
    def authenticate_user2(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_user2.access_token}')
    
    def test_list_categories_not_authenticated(self):
        response = self.client.get(self.category_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_categories_authenticated(self):
        self.authenticate_user1()
        response = self.client.get(self.category_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
from django.db import IntegrityError
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from transaction.models import Transaction, Category


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'type', 'amount', 'date', 'description', 'category')


class CategorySerializer(serializers.ModelSerializer):    
    def create(self, validated_data):
        validated_data['is_system'] = False
        return super().create(validated_data)

    class Meta:
        model = Category
        fields = ('id', 'name', 'type', 'is_system')


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'password2', 'firstname', 'lastname']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = get_user_model().objects.create(**validated_data)
        return user
        
    

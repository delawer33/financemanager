from __future__ import annotations
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')

        user = self.model(
            email=UserManager.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        user = self.model(
            email=UserManager.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.is_admin = True
        user.is_superuser = True
        user.save()
        return user


class Currency(models.Model):
    name = models.CharField(
        'Name',
        max_length=50
    )

    symbol = models.CharField(
        'Symbol',
        max_length=2
    )

    def __str__(self):
        return self.symbol

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class UserModel(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        'Email',
        max_length=255,
        unique=True,
        db_index=True
    )

    firstname = models.CharField(
        'First name',
        max_length=50,
        null=True,
        blank=True
    )

    lastname = models.CharField(
        'Last name',
        max_length=50,
        null=True,
        blank=True
    )

    currency = models.ForeignKey(
        Currency,
        on_delete=models.SET_DEFAULT,
        default=1
    )

    is_active = models.BooleanField(
        'Active',
        default=True
    )

    is_admin = models.BooleanField(
        'Admin',
        default=False
    )

    @property
    def is_staff(self):
        return self.is_superuser

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


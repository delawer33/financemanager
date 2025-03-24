from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Type(models.TextChoices):
    INCOME = "INCOME", "Income"
    OUTCOME = "OUTCOME", "Outcome"


class ReccuringTransactionFrequency(models.TextChoices):
    DAILY = 'daily', 'Daily'
    WEEKLY = 'weekly', 'Weekly'
    MONTHLY = 'monthly', 'Monthly'
    YEARLY = 'yearly', 'Yearly'


class Category(models.Model):
    name = models.CharField(
        'Name',
        max_length=50
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    is_system = models.BooleanField(
        default=False
    )

    type = models.CharField(
        "Type",
        max_length=20,
        choices=Type.choices,
        default=Type.OUTCOME
    )

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        unique_together = [['user', 'name']]


class Transaction(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    type = models.CharField(
        "Type",
        max_length=20,
        choices=Type.choices,
        default=Type.OUTCOME
    )

    amount = models.DecimalField(
        max_digits=16,
        decimal_places=2
    )

    date = models.DateField(
        default=timezone.now
    )

    description = models.TextField(
        max_length=255,
        null=True,
        blank=True
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=True
    )

    def clean(self):
        if self.category and self.category.type != self.type:
            raise ValidationError(
                f"Category '{self.category.name}' does not match Transaction "
                f"type '{self.type}'"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (f'Transaction '
                f'type: {self.type}, '
                f'category: {self.category}, '
                f'date: {self.date}')


class RecurringTransaction(models.Model):
    user = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=16,
        decimal_places=2
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    type = models.CharField(
        "Type",
        max_length=20,
        choices=Type.choices,
        default=Type.OUTCOME
    )

    description = models.TextField(
        max_length=255,
        null=True,
        blank=True
    )

    start_date = models.DateField(
        default=timezone.now,
    )
    
    end_date = models.DateField(
        null=True,
        blank=True
    )

    frequency = models.CharField(
        max_length=10,
        choices=ReccuringTransactionFrequency.choices,
        default=ReccuringTransactionFrequency.MONTHLY
    )

    def __str__(self):
        return f'{self.amount}, {self.category}, {self.type}'

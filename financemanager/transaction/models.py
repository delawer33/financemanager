from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from decimal import Decimal

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
        unique_together = (('name', 'user'),)
        verbose_name_plural = "Categories"



class Account(models.Model):
    """Счёт пользователя (банковский счёт, наличные, карта и т.д.)"""
    
    ACCOUNT_TYPES = [
        ('BANK', 'Bank Account'),
        ('CASH', 'Cash'),
        ('CREDIT_CARD', 'Credit Card'),
        ('INVESTMENT', 'Investment Account'),
        ('SAVINGS', 'Savings Account'),
        ('WALLET', 'Digital Wallet'),
    ]
    
    name = models.CharField('Account Name', max_length=100)
    account_type = models.CharField('Type', max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField('Current Balance', max_digits=16, decimal_places=2, default=0)
    initial_balance = models.DecimalField('Initial Balance', max_digits=16, decimal_places=2, default=0)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='accounts')
    currency = models.CharField('Currency', max_length=3, default='USD')  # ISO код валюты
    is_active = models.BooleanField('Active', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('name', 'user')
        ordering = ['name']
    
    def __str__(self):
        return f'{self.name} ({self.get_account_type_display()})'
    
    def update_balance(self):
        """Пересчитывает баланс на основе транзакций"""
        from django.db.models import Sum, Q
        
        income = Transaction.objects.filter(
            account=self, 
            type=Type.INCOME
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        outcome = Transaction.objects.filter(
            account=self, 
            type=Type.OUTCOME
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        self.balance = self.initial_balance + income - outcome
        self.save(update_fields=['balance'])


class Budget(models.Model):
    """Бюджет пользователя на определённый период"""
    
    PERIOD_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
        ('CUSTOM', 'Custom Period'),
    ]
    
    name = models.CharField('Budget Name', max_length=100)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='budgets')
    period_type = models.CharField('Period Type', max_length=20, choices=PERIOD_CHOICES)
    start_date = models.DateField('Start Date')
    end_date = models.DateField('End Date')
    total_income_limit = models.DecimalField('Total Income Limit', max_digits=16, decimal_places=2, null=True, blank=True)
    total_expense_limit = models.DecimalField('Total Expense Limit', max_digits=16, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField('Active', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f'{self.name} ({self.start_date} - {self.end_date})'
    
    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError('End date must be after start date')
    
    def get_spent_amount(self):
        """Возвращает потраченную сумму в рамках бюджета"""
        return Transaction.objects.filter(
            user=self.user,
            type=Type.OUTCOME,
            date__range=[self.start_date, self.end_date]
        ).aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')
    
    def get_income_amount(self):
        """Возвращает сумму доходов в рамках бюджета"""
        return Transaction.objects.filter(
            user=self.user,
            type=Type.INCOME,
            date__range=[self.start_date, self.end_date]
        ).aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')
    
    def get_remaining_budget(self):
        """Возвращает оставшийся бюджет"""
        if self.total_expense_limit:
            return self.total_expense_limit - self.get_spent_amount()
        return None


class BudgetCategoryLimit(models.Model):
    """Лимиты по категориям в рамках бюджета"""
    
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='category_limits')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    limit_amount = models.DecimalField('Limit Amount', max_digits=16, decimal_places=2)
    
    class Meta:
        unique_together = ('budget', 'category')
    
    def __str__(self):
        return f'{self.budget.name} - {self.category.name}: {self.limit_amount}'
    
    def get_spent_amount(self):
        """Возвращает потраченную сумму по этой категории в рамках бюджета"""
        return Transaction.objects.filter(
            user=self.budget.user,
            category=self.category,
            type=Type.OUTCOME,
            date__range=[self.budget.start_date, self.budget.end_date]
        ).aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')
    
    def get_remaining_limit(self):
        """Возвращает оставшийся лимит по категории"""
        return self.limit_amount - self.get_spent_amount()


# Обновляем существующую модель Transaction
class Transaction(models.Model):
    # Добавляем поле account
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,  # Для совместимости с существующими данными
        blank=True
    )
    
    # Остальные поля остаются без изменений
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField("Type", max_length=20, choices=Type.choices, default=Type.OUTCOME)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.TextField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True)
    
    def clean(self):
        if self.category and self.category.type != self.type:
            raise ValidationError(
                f"Category '{self.category.name}' does not match Transaction "
                f"type '{self.type}'"
            )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        # Обновляем баланс счёта после сохранения транзакции
        if self.account:
            self.account.update_balance()
    
    def __str__(self):
        return (f'Transaction '
                f'type: {self.type}, '
                f'category: {self.category}, '
                f'date: {self.date}')


# Обновляем RecurringTransaction
class RecurringTransaction(models.Model):
    # Добавляем поле account
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='recurring_transactions',
        null=True,
        blank=True
    )
    
    # Остальные поля остаются без изменений
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField("Type", max_length=20, choices=Type.choices, default=Type.OUTCOME)
    description = models.TextField(max_length=255, null=True, blank=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    frequency = models.CharField(
        max_length=10,
        choices=ReccuringTransactionFrequency.choices,
        default=ReccuringTransactionFrequency.MONTHLY
    )
    
    def __str__(self):
        return f'{self.amount}, {self.category}, {self.type}'

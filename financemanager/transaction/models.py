from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

class Type(models.TextChoices):
    INCOME = "INCOME", _("Income")
    OUTCOME = "OUTCOME", _("Outcome")


class ReccuringTransactionFrequency(models.TextChoices):
    DAILY = 'daily', _('Daily')
    WEEKLY = 'weekly', _('Weekly')
    MONTHLY = 'monthly', _('Monthly')
    YEARLY = 'yearly', _('Yearly')

# Словарь переводов для системных категорий
SYSTEM_CATEGORY_LABELS = {
    # OUTCOME categories
    'food_dining': _("Food & Dining"),
    'transportation': _("Transportation"),
    'shopping': _("Shopping"),
    'bills_utilities': _("Bills & Utilities"),
    'entertainment': _("Entertainment"),
    'healthcare': _("Healthcare"),
    'education': _("Education"),
    'travel': _("Travel"),
    'personal_care': _("Personal Care"),
    'gifts_donations': _("Gifts & Donations"),
    'home_garden': _("Home & Garden"),
    'insurance': _("Insurance"),
    'taxes': _("Taxes"),
    'other_expenses': _("Other Expenses"),
    # INCOME categories
    'salary': _("Salary"),
    'freelance': _("Freelance"),
    'investment': _("Investment"),
    'rental_income': _("Rental Income"),
    'business': _("Business"),
    'gifts': _("Gifts"),
    'other_income': _("Other Income"),
}

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


    @property
    def translated_name(self):
        """Возвращает переведенное название категории"""
        if self.is_system and self.name in SYSTEM_CATEGORY_LABELS:
            return str(SYSTEM_CATEGORY_LABELS[self.name])
        return self.name

    def __str__(self):
        return self.translated_name
    
    class Meta:
        unique_together = (('name', 'user'),)
        verbose_name_plural = "Categories"



class Account(models.Model):
    ACCOUNT_TYPES = [
        ('BANK', _('Bank Account')),
        ('CASH', _('Cash')),
        ('CREDIT_CARD', _('Credit Card')),
        ('INVESTMENT', _('Investment Account')),
        ('SAVINGS', _('Savings Account')),
        ('WALLET', _('Digital Wallet')),
    ]
    
    name = models.CharField('Account Name', max_length=100)
    account_type = models.CharField('Type', max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField('Current Balance', max_digits=16, decimal_places=2, default=0)
    initial_balance = models.DecimalField('Initial Balance', max_digits=16, decimal_places=2, default=0)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='accounts')
    is_active = models.BooleanField('Active', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('name', 'user')
        ordering = ['name']
    
    def __str__(self):
        return f'{self.name} ({self.get_account_type_display()})'
    
    def update_balance(self):
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
    PERIOD_CHOICES = [
        ('MONTHLY', _('Monthly')),
        ('QUARTERLY', _('Quarterly')),
        ('YEARLY', _('Yearly')),
        ('CUSTOM', _('Custom Period')),
    ]
    
    name = models.CharField('Budget Name', max_length=100)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='budgets')
    period_type = models.CharField('Period Type', max_length=20, choices=PERIOD_CHOICES)
    start_date = models.DateField('Start Date')
    end_date = models.DateField('End Date')
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
        return Transaction.objects.filter(
            user=self.user,
            type=Type.OUTCOME,
            date__range=[self.start_date, self.end_date]
        ).aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')
    
    def get_income_amount(self):
        return Transaction.objects.filter(
            user=self.user,
            type=Type.INCOME,
            date__range=[self.start_date, self.end_date]
        ).aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')
    
    def get_remaining_budget(self):
        if self.total_expense_limit:
            return self.total_expense_limit - self.get_spent_amount()
        return None


class BudgetCategoryLimit(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='category_limits')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    limit_amount = models.DecimalField('Limit Amount', max_digits=16, decimal_places=2)
    
    class Meta:
        unique_together = ('budget', 'category')
    
    def __str__(self):
        return f'{self.budget.name} - {self.category.translated_name}: {self.limit_amount}'
    
    def get_spent_amount(self):
        return Transaction.objects.filter(
            user=self.budget.user,
            category=self.category,
            type=Type.OUTCOME,
            date__range=[self.budget.start_date, self.budget.end_date]
        ).aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')
    
    def get_remaining_limit(self):
        return self.limit_amount - self.get_spent_amount()


class Transaction(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True
    )
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField("Type", max_length=20, choices=Type.choices, default=Type.OUTCOME)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.TextField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True)
    
    def clean(self):
        if self.category and self.category.type != self.type:
            raise ValidationError(
                f"Category '{self.category.translated_name}' does not match Transaction "
                f"type '{self.type}'"
            )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        if self.account:
            self.account.update_balance()
    
    def __str__(self):
        return (f'Transaction '
                f'type: {self.type}, '
                f'category: {self.category}, '
                f'date: {self.date}')


class RecurringTransaction(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='recurring_transactions',
        null=True,
        blank=True
    )
    
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

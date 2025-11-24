from django import forms
from django.utils import timezone
from django.forms import inlineformset_factory

from .models import Transaction, Category, RecurringTransaction, Account, Budget, BudgetCategoryLimit


class TransactionCreateForm(forms.ModelForm):

    date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'value': timezone.now().date()
            }
        )
    )

    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['category'] = Category.objects.filter(type="OUTCOME")

    def save(self, commit=True):
        trans = super().save(commit=False)
        if commit:
            trans.save()
        return trans

    class Meta:
        model = Transaction
        fields = ('account', 'category', 'date', 'type', 'amount', 'description')
    

class CategoryForm(forms.ModelForm):

    def save(self, commit=True):
        category = super().save(commit=False)
        if commit:
            category.save()
        return category
    
    class Meta:
        model = Category
        fields = ("type", "name")


class RecuringTransactionForm(forms.ModelForm):

    start_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'value': timezone.now().date()
            }
        )
    )

    end_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
            }
        ),
        required=False
    )

    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = RecurringTransaction
        fields = ['account', 'amount', 'type', 'category', 'description', 'start_date', 'end_date', 'frequency']


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'account_type', 'initial_balance', 'currency']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-control'}),
            'initial_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
        }


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['name', 'period_type', 'start_date', 'end_date', 
                 'total_income_limit', 'total_expense_limit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'period_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_income_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_expense_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


BudgetCategoryLimitFormSet = inlineformset_factory(
    Budget, BudgetCategoryLimit,
    fields=['category', 'limit_amount'],
    extra=0,
    can_delete=True
)


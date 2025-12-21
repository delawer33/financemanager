from django import forms
from django.utils import timezone
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.db.models import Q

from .models import Transaction, Category, RecurringTransaction, Account, Budget, BudgetCategoryLimit, Type


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
        fields = ['name', 'account_type', 'initial_balance']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-control'}),
            'initial_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class AccountUpdateForm(forms.ModelForm):
    name = forms.CharField(required=False)
    account_type = forms.ChoiceField(required=False, choices=Account.ACCOUNT_TYPES)
    class Meta:
        model = Account
        fields = ['name', 'account_type']
        widgets = {
            'name': forms.TextInput( attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-control'}),
        }


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['name', 'period_type', 'start_date', 'end_date', 'total_expense_limit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'period_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_expense_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class BudgetCategoryLimitFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Ограничиваем queryset категорий только OUTCOME
        user = self.instance.user if self.instance and self.instance.user else self.user
        if user:
            category_queryset = Category.objects.filter(
                Q(is_system=True) | Q(user=user),
                type=Type.OUTCOME
            ).order_by('name')
        else:
            category_queryset = Category.objects.filter(type=Type.OUTCOME).order_by('name')
        
        for form in self.forms:
            form.fields['category'].queryset = category_queryset


BudgetCategoryLimitFormSet = inlineformset_factory(
    Budget, BudgetCategoryLimit,
    formset=BudgetCategoryLimitFormSet,
    fields=['category', 'limit_amount'],
    extra=0,
    can_delete=True
)


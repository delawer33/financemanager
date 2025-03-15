from django import forms
from django.utils import timezone

from .models import Transaction, Category


class TransactionCreateForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'value': timezone.now().date()
            }
        )
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
        fields = ('category', 'date', 'type', 'amount', 'description')
    

class CategoryForm(forms.ModelForm):

    def save(self, commit=True):
        category = super().save(commit=False)
        if commit:
            category.save()
        return category
    
    class Meta:
        model = Category
        fields = ("type", "name")


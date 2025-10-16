from django_filters import DateFilter, FilterSet, Filter, OrderingFilter, ModelChoiceFilter
from django_filters.widgets import RangeWidget
from django.forms import DateInput
from django.db.models import Q

from .models import Transaction, Account


class DescriptionFilter(Filter):
    def filter(self, qs, value):
        if value:
            qs = qs.filter(Q(description__icontains=value))
        return qs


class CategoryFilter(Filter):
    def filter(self, qs, value):
        if value and value != "Nocategory":
            if value == "Other":
                qs = qs.filter(category=None)
            else:
                qs = qs.filter(category=value)
        return qs


class TransactionFilter(FilterSet):
    # date = DateFromToRangeFilter(widget=RangeWidget(attrs={'type': 'date'}))
    account = ModelChoiceFilter(
        queryset=Account.objects.none(),  # будет обновлено динамически
        label='Account',
        empty_label='---------',
        field_name='account',
        lookup_expr='exact'
    )

    date_from = DateFilter(
        field_name='date', 
        lookup_expr='gte', 
        widget=DateInput(attrs={'type': 'date'})
    )
    date_to = DateFilter(
        field_name='date', 
        lookup_expr='lte', 
        widget=DateInput(attrs={'type': 'date'})
    )
    description = DescriptionFilter()
    category = CategoryFilter()
    sort_by = OrderingFilter(
        fields=(
            ('date', 'date'),
            ('amount', 'amount')
        )
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.filters['account'].queryset = Account.objects.filter(user=user, is_active=True)


    class Meta:
        model = Transaction
        fields = ['type', 'category', 'account', 'date_from', 'date_to', 'sort_by', 'description']
from django_filters import FilterSet, DateFromToRangeFilter, Filter, OrderingFilter
from django_filters.widgets import RangeWidget
from django.db.models import Q

from .models import Transaction


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
    date = DateFromToRangeFilter(widget=RangeWidget(attrs={'type': 'date'}))
    description = DescriptionFilter()
    category = CategoryFilter()
    sort_by = OrderingFilter(
        fields=(
            ('date', 'date'),
            ('amount', 'amount')
        )
    )

    class Meta:
        model = Transaction
        fields = ('type',)

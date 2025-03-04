from django.shortcuts import render

from transaction.filters import TransactionFilter
from transaction.models import Transaction
from diagram.helpers import extended_period_stats


def stats_view(request):
    transaction_filter = TransactionFilter(request.GET, queryset=Transaction.objects)
    transactions = transaction_filter.qs

    data = extended_period_stats(transactions)

    context = {
        'filter': transaction_filter,
        'total_income': data['total_income'],
        'total_expense': data['total_expense'],
        'balance': data['balance'],
        'labels': data['labels'],
        'income_data': data['income_data'],
        'expense_data': data['expense_data'],
        'expense_categories': data['expense_categories'],
        'heatmap': data['heatmap'],
        'weeks_names_for_heatmap': data['weeks_names_for_heatmap'],
        'day_names_for_heatmap': data['day_names_for_heatmap']
    }

    return render(request,
                  'stats.html',
                  context=context)


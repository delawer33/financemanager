from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from transaction.filters import TransactionFilter
from transaction.models import Transaction
from utils.diagram_data import extended_period_stats


@login_required
def stats_view(request):
    transaction_filter = TransactionFilter(
        request.GET, queryset=Transaction.objects.filter(
            user=request.user
        )
    )
    transactions = transaction_filter.qs
    data = extended_period_stats(transactions)
    context = {
        'filter': transaction_filter,
    }
    context.update(data)

    return render(request,
                  'stats.html',
                  context=context)


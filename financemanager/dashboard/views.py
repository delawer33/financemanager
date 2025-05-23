from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required

from transaction.models import Transaction
from utils.diagram_data import period_stats


@login_required
def dashboard(request):
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    qs = Transaction.objects.filter(
        date__range=(start_date, end_date),
        user=request.user
    )

    data = period_stats(qs)

    context = {
        'total_income': data['total_income'],
        'total_expense': data['total_expense'],
        'balance': data['balance'],
        'labels': data['labels'],
        'income_data': data['income_data'],
        'expense_data': data['expense_data'],
        'expense_categories': data['expense_categories'],
    }
    return render(request, 'dashboard/dashboard.html', context)


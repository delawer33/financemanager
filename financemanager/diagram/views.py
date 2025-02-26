from django.shortcuts import render
from datetime import datetime, timedelta

from transaction.models import Transaction
from .helpers import period_stats


# def stats_dynamic_last_month(request):
#     end_date = datetime.now()
#     start_date = end_date.replace(day=1, hour=0, minute=0, second=0)
#
#     data = period_stats(request, start_date, end_date)
#
#     return render(
#         request,
#         'diagram/stats_dynamic_last_month.html',
#         {
#             'month_income': data['month_income'],
#             'month_outcome': data['month_outcome'],
#             'income': data['income'],
#             'outcome': data['outcome'],
#             "labels": data['labels']
#         }
#     )



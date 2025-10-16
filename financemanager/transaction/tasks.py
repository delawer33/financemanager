from celery import shared_task
from django.utils import timezone
from .models import RecurringTransaction, Transaction


@shared_task
def process_recurring_transaction():
    today = timezone.now().date()
    recur_transactions = RecurringTransaction.objects.filter(
        start_date__lte=today
    )
    
    for t in recur_transactions:
        if t.frequency == 'daily' or \
            (t.frequency == 'weekly' 
                and today.weekday() == 0) or \
            (t.frequency == 'monthly' 
                and today.day == t.start_date.day) or \
            (t.frequency == 'yearly' 
                and today.month == t.start_date.month 
                and today.day == t.start_date.day):
            Transaction.objects.create(
                account=t.account,
                user=t.user,
                amount=t.amount,
                type=t.type,
                category=t.category,
                description=t.description,
                date=today
            )

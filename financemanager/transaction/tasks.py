from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import RecurringTransaction, Transaction
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_recurring_transaction():
    try:
        today = timezone.now().date()
        
        try:
            recur_transactions = RecurringTransaction.objects.filter(
                start_date__lte=today
            )
        except Exception as e:
            logger.error(f"Ошибка при получении повторяющихся транзакций: {e}")
            return f"Ошибка: {e}"
        
        created_count = 0
        
        for t in recur_transactions:
            try:
                should_create = False
                
                if t.frequency == 'daily':
                    should_create = True
                elif t.frequency == 'weekly' and today.weekday() == 0:
                    should_create = True
                elif t.frequency == 'monthly' and today.day == t.start_date.day:
                    should_create = True
                elif t.frequency == 'yearly' and today.month == t.start_date.month and today.day == t.start_date.day:
                    should_create = True
                
                if should_create:
                    existing_transaction = Transaction.objects.filter(
                        user=t.user,
                        account=t.account,
                        amount=t.amount,
                        type=t.type,
                        category=t.category,
                        date=today
                    ).first()
                    
                    if not existing_transaction:
                        with transaction.atomic():
                            Transaction.objects.create(
                                account=t.account,
                                user=t.user,
                                amount=t.amount,
                                type=t.type,
                                category=t.category,
                                description=f"{t.description} (автоматически создано)",
                                date=today
                            )
                        created_count += 1
                        logger.info(f"Создана повторяющаяся транзакция для пользователя {t.user.id}")
                        
            except Exception as e:
                logger.error(f"Ошибка при создании транзакции для {t.id}: {e}")
                continue
        
        logger.info(f"Обработка повторяющихся транзакций завершена. Создано: {created_count}")
        return f"Создано транзакций: {created_count}"
        
    except Exception as e:
        logger.error(f"Критическая ошибка в process_recurring_transaction: {e}")
        return f"Критическая ошибка: {e}"

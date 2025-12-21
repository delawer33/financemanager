from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from transaction.models import Account, Category, Type
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate random transactions for user with id=2 for the last 2 months'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of transactions to generate (default: 50)',
        )

    def handle(self, *args, **options):
        user_id = 2
        count = options['count']
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with id={user_id} does not exist')
            )
            return

        # Получаем аккаунты пользователя
        accounts = Account.objects.filter(user=user, is_active=True)
        if not accounts.exists():
            self.stdout.write(
                self.style.ERROR(f'User {user.email} has no active accounts')
            )
            return

        # Получаем категории (системные и пользовательские)
        categories = Category.objects.filter(
            Q(is_system=True) | Q(user=user)
        )
        if not categories.exists():
            self.stdout.write(
                self.style.ERROR(f'No categories found for user {user.email}')
            )
            return

        # Вычисляем даты: от 2 месяцев назад до сегодня
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=60)

        self.stdout.write(
            self.style.SUCCESS(
                f'Generating {count} random transactions for user {user.email} '
                f'(id={user_id}) from {start_date} to {end_date}'
            )
        )

        created_count = 0
        error_count = 0

        # Описания для транзакций
        income_descriptions = [
            'Salary payment',
            'Freelance work',
            'Investment return',
            'Gift received',
            'Bonus payment',
            'Rental income',
            'Business income',
            'Refund',
        ]
        
        outcome_descriptions = [
            'Grocery shopping',
            'Restaurant',
            'Transportation',
            'Shopping',
            'Bills payment',
            'Entertainment',
            'Healthcare',
            'Education',
            'Travel',
            'Personal care',
            'Gifts',
            'Home & Garden',
            'Insurance',
            'Taxes',
        ]

        for i in range(count):
            # Случайная дата в диапазоне
            days_offset = random.randint(0, 60)
            transaction_date = start_date + timedelta(days=days_offset)

            # Случайный аккаунт
            account = random.choice(list(accounts))

            # Случайный тип транзакции (70% расходы, 30% доходы)
            transaction_type = random.choices(
                [Type.OUTCOME, Type.INCOME],
                weights=[70, 30]
            )[0]

            # Случайная категория соответствующего типа
            type_categories = categories.filter(type=transaction_type)
            if not type_categories.exists():
                # Если нет категорий нужного типа, пропускаем
                continue
            category = random.choice(list(type_categories))

            # Случайная сумма
            if transaction_type == Type.INCOME:
                amount = Decimal(str(random.uniform(100, 5000))).quantize(Decimal('0.01'))
                description = random.choice(income_descriptions)
            else:
                amount = Decimal(str(random.uniform(10, 500))).quantize(Decimal('0.01'))
                description = random.choice(outcome_descriptions)

            # Создаем транзакцию через процедуру
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        do $$
                        declare
                            v_transaction_id integer;
                        begin
                            call sp_create_transaction_with_balance_update(
                                %s, %s, %s, %s, %s, %s, %s, v_transaction_id
                            );
                        end $$;
                    """, [
                        user_id,
                        account.id,
                        category.id,
                        transaction_type,
                        amount,
                        transaction_date,
                        description,
                    ])
                created_count += 1
                
                if (i + 1) % 10 == 0:
                    self.stdout.write(
                        f'Created {i + 1}/{count} transactions...'
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Error creating transaction {i + 1}: {str(e)}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} transactions. '
                f'Errors: {error_count}'
            )
        )


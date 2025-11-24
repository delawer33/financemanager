from django.core.management.base import BaseCommand
from transaction.models import Category


class Command(BaseCommand):
    help = 'Initialize default categories'

    def handle(self, *args, **options):
        expense_categories = [
            'Food',
            'Transport',
            'Housing',
            'Utilities',
            'Healthcare',
            'Clothing',
            'Entertainment',
            'Education',
            'Gifts',
            'Electronics',
            'Beauty & Care',
            'Sports & Fitness',
            'Travel',
            'Communication',
            'Taxes',
            'Insurance',
            'Other'
        ]
        
        income_categories = [
            'Salary',
            'Freelance',
            'Investments',
            'Gifts',
            'Tax Refund',
            'Interest',
            'Rental Income',
            'Sale',
            'Other'
        ]
        
        created_count = 0
        
        Category.objects.filter(is_system=True, user=None).delete()
        self.stdout.write(
            self.style.WARNING('Cleared existing system categories')
        )
        
        for category_name in expense_categories:
            category = Category.objects.create(
                name=category_name,
                type='OUTCOME',
                is_system=True,
                user=None
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created expense category: {category.name}')
            )
        
        for category_name in income_categories:
            category = Category.objects.create(
                name=category_name,
                type='INCOME',
                is_system=True,
                user=None
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created income category: {category.name}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully initialized {created_count} default categories')
        )

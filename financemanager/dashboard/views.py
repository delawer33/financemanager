from transaction.forms import BudgetCategoryLimitFormSet
from transaction.models import Transaction, Account, Budget, Category
from django.db.models import Q, Sum
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from utils.diagram_data import period_stats


@login_required
def dashboard(request):
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Транзакции пользователя за период
    qs = Transaction.objects.filter(
        date__range=(start_date, end_date),
        user=request.user
    )
    data = period_stats(qs)

    # Баланс по всем активным счетам пользователя
    accounts = Account.objects.filter(user=request.user, is_active=True)
    total_balance = accounts.aggregate(balance_sum=Sum('balance'))['balance_sum'] or Decimal('0')

    # Текущий активный бюджет (если есть)
    current_budget = Budget.objects.filter(
        user=request.user,
        is_active=True,
        start_date__lte=end_date,
        end_date__gte=start_date
    ).order_by('-start_date').first()

    budget_data = {}
    budget_expense_by_category = []
    budget_categories = Category.objects.none()

    if current_budget:
        spent = current_budget.get_spent_amount()
        income = current_budget.get_income_amount()
        remaining = current_budget.get_remaining_budget()
        budget_limit = current_budget.total_expense_limit
        budget_percentage = (spent / budget_limit * 100) if budget_limit else None

        # Получаем категории бюджета
        budget_categories = Category.objects.filter(
            budgetcategorylimit__budget=current_budget
        ).distinct()

        # Получаем транзакции расходов только по этим категориям
        budget_transactions = Transaction.objects.filter(
            user=request.user,
            date__range=(current_budget.start_date, current_budget.end_date),
            type='OUTCOME',
            category__in=budget_categories
        )

        budget_expense_by_category = (
            budget_transactions
            .values('category__name')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )

        for item in budget_expense_by_category:
            total = item['total']
            limit = budget_limit
            item['usage_percent'] = (total / limit * 100) if limit else 0

        budget_data = {
            'budget': current_budget,
            'budget_spent': spent,
            'budget_income': income,
            'budget_remaining': remaining,
            'budget_limit': budget_limit,
            'budget_percentage': budget_percentage,
            'budget_expense_by_category': budget_expense_by_category,
        }

    # Formset лимитов категорий для создания/редактирования бюджета
    if request.method == 'POST':
        category_limits = BudgetCategoryLimitFormSet(request.POST)
    else:
        category_limits = BudgetCategoryLimitFormSet()

    # Категории для выбора в динамическом добавлении лимитов — только категории бюджета
    categories = budget_categories if current_budget else Category.objects.none()

    context = {
        'total_income': data['total_income'],
        'total_expense': data['total_expense'],
        'balance': total_balance,
        'labels': data['labels'],
        'income_data': data['income_data'],
        'expense_data': data['expense_data'],
        'expense_categories': data['expense_categories'],
        'accounts': accounts,
        **budget_data,
        'category_limits': category_limits,
        'categories': categories,
    }

    return render(request, 'dashboard/dashboard.html', context)

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from transaction.forms import BudgetCategoryLimitFormSet
from transaction.models import Account, Budget, Category, Transaction
from utils.diagram_data import period_stats


@login_required
def dashboard(request):
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    qs = Transaction.objects.filter(
        date__range=(start_date, end_date), user=request.user
    )
    data = period_stats(qs)

    accounts = Account.objects.filter(user=request.user, is_active=True)
    total_balance = accounts.aggregate(balance_sum=Sum("balance"))[
        "balance_sum"
    ] or Decimal("0")

    current_budget = (
        Budget.objects.filter(
            user=request.user,
            is_active=True,
            start_date__lte=end_date,
            end_date__gte=start_date,
        )
        .order_by("-start_date")
        .first()
    )

    budget_data = {}
    budget_expense_by_category = []
    budget_categories = Category.objects.none()

    if current_budget:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    actual_expense, 
                    actual_income, 
                    expense_remaining, 
                    total_expense_limit,
                    expense_percentage_used
                FROM v_budget_execution_report
                WHERE budget_id = %s AND user_id = %s
            """,
                [current_budget.id, request.user.id],
            )

            row = cursor.fetchone()
            if row:
                spent = row[0] or Decimal("0")
                income = row[1] or Decimal("0")
                remaining = row[2]
                budget_limit = row[3]
                budget_percentage = row[4]
            else:
                spent = current_budget.get_spent_amount()
                income = current_budget.get_income_amount()
                remaining = current_budget.get_remaining_budget()
                budget_limit = current_budget.total_expense_limit
                budget_percentage = (
                    (spent / budget_limit * 100) if budget_limit else None
                )

        budget_categories = Category.objects.filter(
            budgetcategorylimit__budget=current_budget
        ).distinct()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    category_name,
                    spent_amount,
                    limit_amount,
                    percentage_used
                FROM fn_check_budget_limits(%s)
                ORDER BY percentage_used DESC
            """,
                [current_budget.id],
            )

            budget_expense_by_category = []
            for row in cursor.fetchall():
                # Получаем категорию по имени для перевода
                category_name = row[0]
                try:
                    category = Category.objects.get(name=category_name, is_system=True)
                    translated_name = category.translated_name
                except Category.DoesNotExist:
                    translated_name = category_name
                
                budget_expense_by_category.append(
                    {
                        "category__name": translated_name,
                        "total": row[1],
                        "limit": row[2],
                        "usage_percent": row[3] or 0,
                    }
                )

        budget_data = {
            "budget": current_budget,
            "budget_spent": spent,
            "budget_income": income,
            "budget_remaining": remaining,
            "budget_limit": budget_limit,
            "budget_percentage": budget_percentage,
            "budget_expense_by_category": budget_expense_by_category,
        }

    if request.method == "POST":
        category_limits = BudgetCategoryLimitFormSet(request.POST)
    else:
        category_limits = BudgetCategoryLimitFormSet()

    categories = budget_categories if current_budget else Category.objects.none()

    context = {
        "total_income": data["total_income"],
        "total_expense": data["total_expense"],
        "balance": total_balance,
        "labels": data["labels"],
        "income_data": data["income_data"],
        "expense_data": data["expense_data"],
        "expense_categories": data["expense_categories"],
        "accounts": accounts,
        **budget_data,
        "category_limits": category_limits,
        "categories": categories,
    }

    return render(request, "dashboard/dashboard.html", context)

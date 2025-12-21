from django.db import IntegrityError, connection
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .filters import TransactionFilter
from .forms import (
    AccountUpdateForm, TransactionCreateForm, CategoryForm, RecuringTransactionForm,
    AccountForm, BudgetForm, BudgetCategoryLimitFormSet
)
from .models import (
    Transaction, Category, RecurringTransaction, 
    Account, Budget, BudgetCategoryLimit, Type
)


class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    template_name = 'transaction/account_list.html'
    context_object_name = 'accounts'
    
    def get_queryset(self):
        return Account.objects.filter(user=self.request.user).order_by('name')


class AccountCreateView(LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'transaction/account_form.html'
    success_url = reverse_lazy('transaction:account-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.balance = form.instance.initial_balance
        messages.success(self.request, 'Account created successfully!')
        return super().form_valid(form)


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountUpdateForm
    template_name = 'transaction/account_form.html'
    success_url = reverse_lazy('transaction:account-list')
    
    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Account updated successfully!')
        return super().form_valid(form)


class AccountDetailView(LoginRequiredMixin, DetailView):
    model = Account
    template_name = 'transaction/account_detail.html'
    context_object_name = 'account'
    
    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.get_object()
        
        transactions = Transaction.objects.filter(
            account=account
        ).select_related('category').order_by('-date')
        
        filter = TransactionFilter(self.request.GET, queryset=transactions)
        
        income_total = transactions.filter(type=Type.INCOME).aggregate(
                Sum('amount'))['amount__sum'] or Decimal('0')
        outcome_total = transactions.filter(type=Type.OUTCOME).aggregate(
                Sum('amount'))['amount__sum'] or Decimal('0')
        net_change = income_total - outcome_total
        context.update({
            'transactions': filter.qs,
            'filter': filter,
            'income_total': income_total,
            'outcome_total': outcome_total,
            'net_change': net_change
        })
        
        return context


@login_required
def account_delete(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    
    if request.method == 'POST':
        transaction_count = Transaction.objects.filter(account=account).count()
        
        if transaction_count > 0:
            messages.error(
                request, 
                f'Cannot delete account "{account.name}". '
                f'It has {transaction_count} associated transactions.'
            )
        else:
            account.delete()
            messages.success(request, f'Account "{account.name}" deleted successfully!')
    
    return redirect('transaction:account-list')


class BudgetListView(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'transaction/budget_list.html'
    context_object_name = 'budgets'
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).order_by('-start_date')


class BudgetCreateView(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'transaction/budget_form.html'
    success_url = reverse_lazy('transaction:budget-list')
    
    def get_initial(self):
        initial = super().get_initial()
        initial['name'] = self.request.GET.get('name', '')
        initial['period_type'] = self.request.GET.get('period_type', '')
        initial['total_expense_limit'] = self.request.GET.get('total_expense_limit', '')
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['category_limits'] = BudgetCategoryLimitFormSet(
                self.request.POST,
                prefix='category_limits',
            )
        else:
            context['category_limits'] = BudgetCategoryLimitFormSet(
                prefix='category_limits',
            )
        context['categories'] = Category.objects.filter(
            Q(is_system=True) | Q(user=self.request.user),
            type=Type.OUTCOME
        ).order_by('name')
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        category_limits = context['category_limits']
        print(category_limits.errors)
        form.instance.user = self.request.user
        
        if category_limits.is_valid():
            self.object = form.save()
            category_limits.instance = self.object
            category_limits.save()
            messages.success(self.request, 'Budget created successfully!')
            return super().form_valid(form)
        else:
            return self.render_to_response(context)


class BudgetDetailView(LoginRequiredMixin, DetailView):
    model = Budget
    template_name = 'transaction/budget_detail.html'
    context_object_name = 'budget'
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        budget = self.get_object()
        
        spent_amount = budget.get_spent_amount()
        income_amount = budget.get_income_amount()
        remaining_budget = budget.get_remaining_budget()
        
        category_limits = BudgetCategoryLimit.objects.filter(budget=budget)
        category_progress = []
        
        for limit in category_limits:
            spent = limit.get_spent_amount()
            remaining = limit.get_remaining_limit()
            percentage = (spent / limit.limit_amount * 100) if limit.limit_amount > 0 else 0
            
            category_progress.append({
                'limit': limit,
                'spent': spent,
                'remaining': remaining,
                'percentage': min(percentage, 100),
                'over_budget': spent > limit.limit_amount,
            })
        
        transactions = Transaction.objects.filter(
            user=self.request.user,
            date__range=[budget.start_date, budget.end_date]
        ).select_related('category', 'account').order_by('-date')
        
        context.update({
            'spent_amount': spent_amount,
            'income_amount': income_amount,
            'remaining_budget': remaining_budget,
            'category_progress': category_progress,
            'transactions': transactions,
            'budget_percentage': (spent_amount / budget.total_expense_limit * 100) 
                               if budget.total_expense_limit and budget.total_expense_limit > 0 else 0,
        })
        
        return context


@login_required
def budget_delete(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    
    if request.method == 'POST':
        budget.delete()
        messages.success(request, f'Budget "{budget.name}" deleted successfully!')
    
    return redirect('transaction:budget-list')


class TransactionCreate(LoginRequiredMixin, CreateView):
    form_class = TransactionCreateForm
    template_name = 'transaction/createtransaction.html'
    success_url = reverse_lazy('transaction:create-trans')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['category'].queryset = Category.objects.filter(
            Q(is_system=True) | Q(user=self.request.user)
        )
        form.fields['account'].queryset = Account.objects.filter(
            user=self.request.user, is_active=True
        )
        return form

    def form_valid(self, form):        
        form.instance.user = self.request.user
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DO $$
                    DECLARE
                        v_transaction_id INTEGER;
                    BEGIN
                        CALL sp_create_transaction_with_balance_update(
                            %s, %s, %s, %s, %s, %s, %s, v_transaction_id
                        );
                    END $$;
                """, [
                    self.request.user.id,
                    form.instance.account.id if form.instance.account else None,
                    form.instance.category.id if form.instance.category else None,
                    form.instance.type,
                    form.instance.amount,
                    form.instance.date,
                    form.instance.description or '',
                ])
            
            messages.success(self.request, 'Transaction created successfully!')
            return redirect(self.success_url)
            
        except Exception as e:            
            messages.error(self.request, f'Error creating transaction: {str(e)}')
            return self.form_invalid(form)


@login_required
def transaction_delete(request, pk):
    trans = get_object_or_404(Transaction, id=pk, user=request.user)
    
    if request.method == 'POST':
        account = trans.account
        trans.delete()
        
        if account:
            account.update_balance()
        
        messages.success(request, 'Transaction deleted successfully!')
    
    list_filter = TransactionFilter(
        request.GET, 
        queryset=Transaction.objects.filter(user=request.user).order_by("-date")
    )
    
    return render(
        request,
        'transaction/transaction_list_part.html',
        {'list_filter': list_filter}
    )


@login_required
def get_categories_by_type(request):
    transaction_type = request.GET.get('type')
    user_categories = Category.objects.filter(
        Q(type=transaction_type) & (Q(is_system=True) | Q(user=request.user))
    )
    return render(
        request,
        'transaction/category_dropdown.html',
        {'categories': user_categories}
    )


@login_required
def get_account_balance(request, account_id):
    try:
        account = Account.objects.get(id=account_id, user=request.user)
        return JsonResponse({
            'balance': float(account.balance),
            'currency': account.currency,
        })
    except Account.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)


@login_required
def budget_progress_api(request, budget_id):
    try:
        budget = Budget.objects.get(id=budget_id, user=request.user)
        
        data = {
            'spent': float(budget.get_spent_amount()),
            'income': float(budget.get_income_amount()),
            'remaining': float(budget.get_remaining_budget() or 0),
            'total_limit': float(budget.total_expense_limit or 0),
        }
        
        return JsonResponse(data)
    except Budget.DoesNotExist:
        return JsonResponse({'error': 'Budget not found'}, status=404)


def get_categories_by_type_for_filter(request):
    transaction_type = request.GET.get('type')
    cur_category = request.GET.get('category')
    if transaction_type != "Notype":
        categories = Category.objects.filter(type=transaction_type)
    else:
        categories = Category.objects.all()
    
    return render(
        request,
        'transaction/category_dropdown_for_filter.html',
        {'categories': categories, 'cur_category': cur_category}
    )


class RecurringTransactionCreate(LoginRequiredMixin, CreateView):
    model = RecurringTransaction
    form_class = RecuringTransactionForm
    template_name = 'transaction/create_recur_trans.html'
    success_url = reverse_lazy('transaction:create-rec-trans')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['account'].queryset = Account.objects.filter(
            user=self.request.user, is_active=True
        )
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['recur_transactions'] = RecurringTransaction.objects.filter(
            user=self.request.user
        ).order_by('-id')
        return ctx


class CategoryView(LoginRequiredMixin, CreateView):
    form_class = CategoryForm
    template_name = 'transaction/create_category.html'
    success_url = reverse_lazy('transaction:category')

    def form_valid(self, form):
        form.instance.user = self.request.user
        try:
            messages.success(self.request, 'Category created successfully!')
            return super().form_valid(form)
        except IntegrityError:
            form.add_error('name', "Category names can't repeat")
            return self.form_invalid(form)
        
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        categories = Category.objects.filter(
            Q(is_system=True) | Q(user=self.request.user)
        )
        ctx['categories'] = categories
        return ctx


@login_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, id=pk, user=request.user)
    
    if request.method == 'POST':
        cat.delete()
        messages.success(request, f'Category "{cat.translated_name}" deleted successfully!')
    
    categories = Category.objects.filter(
        Q(is_system=True) | Q(user=request.user)
    )
    return render(
        request,
        'transaction/category_list.html',
        {'categories': categories}
    )


@login_required
def recur_transaction_delete(request, pk):
    rec_trans = get_object_or_404(RecurringTransaction, id=pk, user=request.user)
    
    if request.method == 'POST':
        rec_trans.delete()
        messages.success(request, 'Recurring transaction deleted successfully!')
    
    qs = RecurringTransaction.objects.filter(
        user=request.user
    ).order_by('-id')

    return render(
        request,
        'transaction/recur_trans_list.html',
        {'recur_transactions': qs}
    )


@login_required
def transaction_list(request):
    filter = TransactionFilter(
        request.GET, 
        queryset=Transaction.objects.filter(user=request.user).order_by("-date"),
        user=request.user
    )
    return render(request, 'transaction/transaction_list.html', {'filter': filter})


@login_required
def transaction_list_part(request):
    list_filter = TransactionFilter(
        request.GET, 
        queryset=Transaction.objects.filter(user=request.user).order_by("-date"),
        user=request.user
    )
    return render(request, 'transaction/transaction_list_part.html', {"list_filter": list_filter})

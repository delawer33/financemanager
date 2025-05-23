from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .filters import TransactionFilter
from .forms import TransactionCreateForm, CategoryForm, RecuringTransactionForm
from .models import Transaction, Category, RecurringTransaction


@login_required
def dashboard(request):
    return render(request, 'transaction/dashboard.html')


def get_categories_by_type(request):
    transaction_type = request.GET.get('type')
    categories = Category.objects.filter(type=transaction_type)
    return render(
        request,
        'transaction/category_dropdown.html',
        {'categories': categories}
    )


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
        {'categories': categories,
         'cur_category': cur_category}
    ) 


class TransactionCreate(LoginRequiredMixin, CreateView):
    form_class = TransactionCreateForm
    template_name = 'transaction/createtransaction.html'
    success_url = reverse_lazy('transaction:create-trans')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['category'].queryset = Category.objects.filter(
            Q(is_system=True) | Q(user=self.request.user)
        )
        return form

    def form_valid(self, form):
        trans = form.save(commit=False)
        trans.user = self.request.user
        return super().form_valid(form)


class RecurringTransactionCreate(LoginRequiredMixin, CreateView):
    model = RecurringTransaction
    form_class = RecuringTransactionForm
    template_name = 'transaction/create_recur_trans.html'
    success_url = reverse_lazy('transaction:create-rec-trans')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['recur_transactions'] = RecurringTransaction.objects.filter(
            user=self.request.user
        )
        ctx['recur_transactions'] = ctx['recur_transactions'].order_by('-id')
        
        return ctx


class CategoryView(LoginRequiredMixin, CreateView):
    form_class = CategoryForm
    template_name = 'transaction/create_category.html'
    success_url = reverse_lazy('transaction:category')

    def form_valid(self, form):
        cat = form.save(commit=False)
        cat.user = self.request.user
        try:
            return super().form_valid(form)
        except IntegrityError as ie:
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
    cat = get_object_or_404(Category, id=pk)
    categories = Category.objects.filter(
        Q(is_system=True) | Q(user=request.user)
    )
    if request.method == 'POST' and cat.user == request.user:
        cat.delete()
    return render(
        request,
        'transaction/category_list.html',
        {
            'categories': categories
        }
    )


@login_required
def transaction_delete(request, pk):
    trans = get_object_or_404(Transaction, id=pk)
    list_filter = TransactionFilter(
        request.POST, 
        queryset=Transaction.objects.filter(user=request.user).order_by("-date")
    )
    
    if request.method == 'POST' and trans.user == request.user:
        trans.delete()
    return render(
        request,
        'transaction/transaction_list_part.html',
        {
            'list_filter': list_filter
        }
    )


@login_required
def recur_transaction_delete(request, pk):
    rec_trans = get_object_or_404(RecurringTransaction, id=pk)
    if request.method == 'POST' and rec_trans.user == request.user:
        rec_trans.delete()
    qs = RecurringTransaction.objects.filter(
        user=request.user
    ).order_by(
        '-id'
    )

    return render(
        request,
        'transaction/recur_trans_list.html',
        {
            'recur_transactions': qs
        }
    )


@login_required
def transaction_list(request):
    filter = TransactionFilter(
        request.GET, 
        queryset=Transaction.objects.filter(user=request.user).order_by("-date")
    )
    return render(request, 'transaction/transaction_list.html', {'filter': filter})


@login_required
def transaction_list_part(request):
    list_filter = TransactionFilter(
        request.GET, 
        queryset=Transaction.objects.filter(user=request.user).order_by("-date")
    )
    return render(request, 'transaction/transaction_list_part.html', {"list_filter": list_filter})


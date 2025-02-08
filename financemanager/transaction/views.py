from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic.list import ListView
from rest_framework import permissions, viewsets, filters
from rest_framework.response import Response

from .filters import TransactionFilter
from .forms import TransactionCreateForm
from .models import Transaction, Category
from .serializers import TransactionSerializer


@login_required
def dashboard(request):
    return render(request, 'transaction/dashboard.html')


def get_categories_by_type(request):
    transaction_type = request.GET.get('type')
    categories = Category.objects.filter(type=transaction_type)
    print(categories)
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
    success_url = reverse_lazy('transaction:dashboard')

    def form_valid(self, form):
        trans = form.save(commit=False)
        trans.user = self.request.user
        return super().form_valid(form)


def transaction_list(request):
    # model = Transaction
    # template_name = 'transaction/history.html'
    # context_object_name = 'transactions'
    # fields = ['category', 'type', 'date', 'amount']
    filter = TransactionFilter(request.GET, queryset=Transaction.objects.order_by("-id"))
    return render(request, 'transaction/transaction_list.html', {'filter': filter})


class TransactionViewset(viewsets.ModelViewSet):
    http_method_names = ['get']
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(user=user).order_by('-id')

    class Meta:
        ordering = ['-id']

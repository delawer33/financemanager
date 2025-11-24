from django.urls import path
from django.views.generic.base import RedirectView

import transaction.views as views

app_name = 'transaction'

urlpatterns = [
    path('', RedirectView.as_view(url="dashboard"), name='dashboard'),
    path('create/', views.TransactionCreate.as_view(), name='create-trans'),
    path('create-rec/', views.RecurringTransactionCreate.as_view(), name='create-rec-trans'),
    path('history/', views.transaction_list, name='trans-list'),
    path('transaction/delete/<pk>', views.transaction_delete, name='trans-delete'),
    path('recur-trans/delete/<pk>', views.recur_transaction_delete, name='recur-trans-delete'),
    path('category/', views.CategoryView.as_view(), name='category'),
    path('category/delete/<pk>', views.category_delete, name='category-delete'),
    path('trans_list_part/', views.transaction_list_part, name='trans-list-part'),
    path('get_categories/', views.get_categories_by_type, name='get-categories'),
    path('get_categories_for_filter/', views.get_categories_by_type_for_filter, name='get-categories-for-filter'),
    path('accounts/', views.AccountListView.as_view(), name='account-list'),
    path('accounts/create/', views.AccountCreateView.as_view(), name='account-create'),
    path('accounts/<int:pk>/', views.AccountDetailView.as_view(), name='account-detail'),
    path('accounts/<int:pk>/edit/', views.AccountUpdateView.as_view(), name='account-update'),
    path('accounts/<int:pk>/delete/', views.account_delete, name='account-delete'),
    
    path('budgets/', views.BudgetListView.as_view(), name='budget-list'),
    path('budgets/create/', views.BudgetCreateView.as_view(), name='budget-create'),
    path('budgets/<int:pk>/', views.BudgetDetailView.as_view(), name='budget-detail'),
    path('budgets/<int:pk>/delete/', views.budget_delete, name='budget-delete'),
    
    path('api/account/<int:account_id>/balance/', views.get_account_balance, name='account-balance-api'),
    path('api/budget/<int:budget_id>/progress/', views.budget_progress_api, name='budget-progress-api'),
    
]

from django.urls import path, include
from django.views.generic.base import RedirectView
from rest_framework.routers import DefaultRouter

from .views import (
    dashboard,
    TransactionCreate,
    CategoryView,
    transaction_list,
    transaction_delete,
    category_delete,
    transaction_list_part,
    TransactionViewset,
    get_categories_by_type,
    get_categories_by_type_for_filter,
)


app_name = 'transaction'

router = DefaultRouter()
router.register('transactions', TransactionViewset)

urlpatterns = [
    path('', RedirectView.as_view(url="dashboard"), name='dashboard'),
    path('create/', TransactionCreate.as_view(), name='create-trans'),
    path('history/', transaction_list, name='trans-list'),
    path('transaction/delete/<pk>', transaction_delete, name='trans-delete'),
    path('category/', CategoryView.as_view(), name='category'),
    path('category/delete/<pk>', category_delete, name='category-delete'),
    path('trans_list_part/', transaction_list_part, name='trans-list-part'),
    path('get_categories/', get_categories_by_type, name='get-categories'),
    path('get_categories_for_filter/', get_categories_by_type_for_filter, name='get-categories-for-filter'),
    path('api/', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    dashboard,
    TransactionCreate,
    transaction_list,
    TransactionViewset,
    get_categories_by_type,
    get_categories_by_type_for_filter,
)


app_name = 'transaction'

router = DefaultRouter()
router.register('transactions', TransactionViewset)

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('create/', TransactionCreate.as_view(), name='create-trans'),
    path('history/', transaction_list, name='trans-list'),
    path('get_categories/', get_categories_by_type, name='get-categories'),
    path('get_categories_for_filter/', get_categories_by_type_for_filter, name='get-categories-for-filter'),
    path('api/', include(router.urls)),
]

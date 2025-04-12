from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from .views import (
    TransactionViewset, 
    CategoryViewset,
    RegisterViewAPI
)


router = DefaultRouter()
router.register('transactions', TransactionViewset, basename='api-transactions')
router.register('categories', CategoryViewset, basename='api-categories')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterViewAPI.as_view(), name='api-auth-register'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

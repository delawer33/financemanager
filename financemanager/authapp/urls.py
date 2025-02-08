from django.urls import path, include

from .views import RegisterView, LoginView, LogoutView

app_name = 'authapp'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('api-auth/', include('rest_framework.urls', namespace='api-auth')),
]

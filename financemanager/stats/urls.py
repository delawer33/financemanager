from django.urls import path, include


from .views import stats_view

app_name = 'stats'

urlpatterns = [
    path('', stats_view, name='stats'),
]

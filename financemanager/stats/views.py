from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from transaction.filters import TransactionFilter
from transaction.models import Transaction
from utils.diagram_data import extended_period_stats


def get_stats_cache_key(user_id, query_string):
    return f'user_stats_{user_id}_{hash(query_string)}'


@receiver([post_delete, post_save], sender=Transaction)
def invalidate_stats_cache(sender, instance, **kwargs):
    if hasattr(instance, 'user'):
        user_id = instance.user.id
        cache_keys_list_key = f'user_stats_keys_{user_id}'
        
        active_keys = cache.get(cache_keys_list_key) or []
        
        for key in active_keys:
            cache.delete(key)
        
        cache.delete(cache_keys_list_key)


@login_required
def stats_view(request):
    transaction_filter = TransactionFilter(
        request.GET, queryset=Transaction.objects.filter(
            user=request.user
        ).select_related('category', 'account')
    )
    transactions = transaction_filter.qs
    
    query_string = request.GET.urlencode()
    cache_key = get_stats_cache_key(request.user.id, query_string)
    
    data = cache.get(cache_key)
    
    if data is None:
        data = extended_period_stats(transactions)
        cache.set(cache_key, data, 45)
        
        cache_keys_list_key = f'user_stats_keys_{request.user.id}'
        active_keys = cache.get(cache_keys_list_key)
        if not active_keys:
            active_keys = []
        if cache_key not in active_keys:
            active_keys.append(cache_key)
            cache.set(cache_keys_list_key, active_keys, 60)
    
    context = {
        'filter': transaction_filter,
    }
    context.update(data)

    return render(request,
                  'stats/stats.html',
                  context=context)


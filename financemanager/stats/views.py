from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from transaction.filters import TransactionFilter
from transaction.models import Transaction
from utils.diagram_data import extended_period_stats


def get_stats_cache_key(user_id):
    return f'user_stats_{user_id}'


@receiver([post_delete, post_save], sender=Transaction)
def invalidate_stats_cache(sender, instance, **kwargs):
    if hasattr(instance, 'user'):
        cache.delete(get_stats_cache_key(instance.user.id))


@login_required
def stats_view(request):
    cache_key = get_stats_cache_key(request.user.id)
    data = cache.get(cache_key)
    transaction_filter = TransactionFilter(
        request.GET, queryset=Transaction.objects.filter(
            user=request.user
        )
    )
    transactions = transaction_filter.qs
    if not data:
        data = extended_period_stats(transactions)
        cache.set(cache_key, data, 60 * 60 * 24 * 7)
    context = {
        'filter': transaction_filter,
    }
    context.update(data)

    return render(request,
                  'stats/stats.html',
                  context=context)


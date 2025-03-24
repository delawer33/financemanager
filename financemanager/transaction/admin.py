from django.contrib import admin

from .models import Transaction, Category, RecurringTransaction


class TransactionAdmin(admin.ModelAdmin):
    pass


class CategoryAdmin(admin.ModelAdmin):
    pass


class RecurringTransactionAdmin(admin.ModelAdmin):
    pass


admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(RecurringTransaction, RecurringTransactionAdmin)

from django.contrib import admin

from .models import Transaction, Category, RecurringTransaction, Account, Budget


class TransactionAdmin(admin.ModelAdmin):
    pass


class CategoryAdmin(admin.ModelAdmin):
    pass


class RecurringTransactionAdmin(admin.ModelAdmin):
    pass


class AccountAdmin(admin.ModelAdmin):
    pass


class BudgetAdmin(admin.ModelAdmin):
    pass


admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(RecurringTransaction, RecurringTransactionAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Budget, BudgetAdmin)

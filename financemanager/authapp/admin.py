from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import UserModel
from .forms import UserCreationForm, UserChangeForm


class UserAdmin(BaseUserAdmin):
    # form = UserChangeForm
    # add_form = UserCreationForm

    list_display = [
        'email',
        'firstname',
        'lastname',
        'is_admin'
    ]

    ordering = ('email', )

    list_filter = ('is_admin',)

    fieldsets = (
        (None, {'fields': ['email', 'password', 'currency']}),
        ('Personal Info', {'fields': ['firstname', 'lastname']}),
        ('Permissions', {'fields': ['is_admin']})
    )

    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["email", "password1", "password2"],
            },
        ),
    ]

    search_fields = ('email',)


admin.site.register(UserModel, UserAdmin)
admin.site.unregister(Group)

"""
Django admin customisation
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from core import models

class UserAdmin(BaseUserAdmin):
    ordering = ['id']
    list_display = ("email",'name')
    fieldsets = (
        (None, {'fields' : ('email','password')}),
        (
            _('Permissions'),
            {
                'fields' : (
                    'is_active',
                    'is_staff',
                    'is_superuser'
                )
            }
        ),
        (_('Important dates'), {'fields' : ('last_login',)})
    )
    readonly_fields = ['last_login']
    add_fieldsets = (
        (
            None,
            {
                'classes' : (
                    'wide'
                ),
                'fields' : (
                    'email',
                    'password1',
                    'password2',
                    'name',
                    'is_active',
                    'is_staff',
                    'is_superuser'
                )
            }
        ),
    )



"""
si aggiunge user UserAdmin per indicare che vogliamo anche le indicazioni fornite in quella classe
come per esempio l'order e la list_display
"""
admin.site.register(models.User, UserAdmin)
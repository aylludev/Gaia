from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from hades.models import User

# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'dni', 'email', 'is_active')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    fieldsets = UserAdmin.fieldsets + (('Information Adicional', {'fields': ('dni', 'image')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Information Adicional', {'fields': ('dni', 'image')}),)

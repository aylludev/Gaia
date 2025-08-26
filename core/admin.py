from django.contrib import admin
from core.models import Currency

# Register your models here.
@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'exchange_rate_to_base')
    search_fields = ('code', 'name')
    list_filter = ('code',)
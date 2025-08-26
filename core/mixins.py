# core/mixins.py
from django.utils.functional import cached_property
from core.models import Currency

class CurrencyContextMixin:
    @cached_property
    def selected_currency(self):
        code = self.request.session.get('currency', 'COP')
        return Currency.objects.filter(code=code).first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        currency = self.selected_currency
        context['selected_currency'] = currency
        context['exchange_rate'] = currency.exchange_rate_to_base if currency else 1
        return context

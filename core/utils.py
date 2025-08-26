# utils.py
from .models import Currency

def get_exchange_rate(request):
    code = request.session.get('currency', 'COP')  # Por defecto COP
    currency = Currency.objects.filter(code=code).first()
    if currency:
        return currency.exchange_rate_to_base
    return 1.0  # Si no encuentra, asumimos 1.0


def convert_price(price, request):
    try:
        currency_code = request.session.get('currency', 'COP')  # Default: COP
        if currency_code == 'COP':
            return round(float(price), 2)

        currency = Currency.objects.get(code=currency_code)
        rate = currency.exchange_rate_to_base
        return round(float(price) / float(rate), 2)
    except Currency.DoesNotExist:
        return round(float(price), 2)

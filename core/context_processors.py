from .models import Currency

def currency_context(request):
    currencies = Currency.objects.all()
    selected_code = request.session.get('currency', None)
    selected_currency = Currency.objects.filter(code=selected_code).first() if selected_code else None
    return {
        'currencies': currencies,
        'selected_currency': selected_currency,
    }

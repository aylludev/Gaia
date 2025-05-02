from django import forms
from django.forms import ModelForm
from datetime import datetime
from hermes.models import PurchasePayment, SalePayment, CashClosing

class PurchasePaymentForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].widget.attrs['autofocus'] = True

    class Meta:
        model = PurchasePayment
        fields = '__all__'
        widgets = {
            'amount': forms.NumberInput(attrs={'placeholder': '', 'class': 'form-control', 'autocomplete': 'off', 'autofocus': True}),
            'invoice': forms.TextInput(attrs={'placeholder': 'Factura', 'class': 'form-control', 'autocomplete': 'off'}),
            'days_to_expiration': forms.NumberInput(attrs={'placeholder': 'Días de vencimiento', 'class': 'form-control', 'autocomplete': 'off'}),
            'payment_date': forms.DateInput(format='%Y-%m-%d', attrs={'value': datetime.now().strftime('%Y-%m-%d'), 'autocomplete': 'off', 'class': 'form-control datetimepicker-input datetimepiker4', 'id': 'date_joined', 'data-target': '#date_joined', 'data-toggle': 'datetimepicker' }),
            'note': forms.TextInput(attrs={'placeholder': 'Observaciones', 'class': 'form-control', 'autocomplete': 'off'}),
        }
        exclude = ['created_at', 'updated_at', 'created_by', 'updated_by', 'purchase']

    def save(self, commit=True):
        data = {}
        form = super()
        try:
            if form.is_valid():
                instance = form.save()
                data = instance.to_json()
            else:
                data['error'] = form.errors
        except Exception as e:
            data['error'] = str(e)
        return data

class SalePaymentForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].widget.attrs['autofocus'] = True            

    class Meta:
        model = SalePayment
        fields = '__all__'
        widgets = {
            'amount': forms.NumberInput(attrs={'placeholder': '', 'class': 'form-control', 'autocomplete': 'off', 'autofocus': True}),
            'invoice': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'readonly': True, 'value': ''}),
            'days_to_expiration': forms.NumberInput(attrs={'placeholder': 'Días de vencimiento', 'class': 'form-control', 'autocomplete': 'off'}),
            'note': forms.TextInput(attrs={'placeholder': 'Observaciones', 'class': 'form-control', 'autocomplete': 'off'}),
        }
        exclude = ['created_at', 'updated_at', 'created_by', 'updated_by', 'sale', 'payment_date']

    def save(self, commit=True):
        data = {}
        form = super()
        try:
            if form.is_valid():
                instance = form.save()
                data = instance.to_json()
            else:
                data['error'] = form.errors
        except Exception as e:
            data['error'] = str(e)
        return data

class CashClosingForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['observations'].widget.attrs['autofocus'] = True

    class Meta:
        model = CashClosing
        fields = '__all__'
        widgets = {
            'observations': forms.TextInput(attrs={'placeholder': 'Observaciones', 'class': 'form-control', 'autocomplete': 'off'}),
        }
        exclude = ['created_at', 'updated_at', 'created_by', 'updated_by', 'last_login', 'date', 'total_cash']

    def save(self, commit=True):
        data = {}
        form = super()
        try:
            if form.is_valid():
                form.save()
            else:
                data['error'] = form.errors
        except Exception as e:
            data['error'] = str(e)
        return data
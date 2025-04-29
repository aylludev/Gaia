from django.forms import ModelForm
from django import forms
from artemisa.models import Category, Product, UnitMeasure, PriceHistory, Provider, Purchase
from datetime import datetime

class CategoryForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = True

    class Meta:
        model = Category
        fields = 'name', 'desc'
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ingrese un nombre', }),
            'desc': forms.Textarea(attrs={'placeholder': 'Ingrese un nombre', 'rows': 3, 'cols': 3 }),
        }

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

class UnitMeasureForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs['autofocus'] = True

    class Meta:
        model = UnitMeasure
        fields = 'quantity', 'unit'
        widgets = {
            'quantity': forms.NumberInput(attrs={'placeholder': 'Ingrese la Cantidad', }),
            'unit': forms.Select(attrs={'class': 'select2', 'style': 'width: 100%'}),
        }

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


class ProductForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = True

    class Meta:
        model = Product
        fields = 'code', 'name', 'unit', 'cat', 'stock', 'purchase_price', 'sale_price'
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ingrese un nombre',}),
            'cat': forms.Select(attrs={'class': 'select2', 'style': 'width: 100%'}),
        }

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

class ProviderForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['names'].widget.attrs['autofocus'] = True

    class Meta:
        model = Provider
        fields = 'names', 'dni', 'email', 'address', 'city', 'cellphone', 'observation'
        widgets = {
            'names': forms.TextInput(attrs={'placeholder': 'Ingrese sus nombres',}),
            'dni': forms.TextInput(attrs={'placeholder': 'Ingrese su dni',}),
            'email': forms.TextInput(attrs={'placeholder': 'Ingrese su email',}),
            'address': forms.TextInput(attrs={'placeholder': 'Ingrese su dirección', }),
            'city': forms.TextInput(attrs={'placeholder': 'Ingrese su ciudad',}),
            'cellphone': forms.TextInput(attrs={'placeholder': 'Ingrese su celular',}),
            'observation': forms.TextInput(attrs={'placeholder': 'Observaciones',}),
        }

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


class PriceHistoryForm(ModelForm):

    class Meta:
        model = PriceHistory
        fields = '__all__'

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

class PurchaseForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['provider'].queryset = Provider.objects.none()

    class Meta:
        model = Purchase
        fields = '__all__'
        widgets = {
            'invoice_number': forms.TextInput(attrs={'placeholder': 'Ingrese el numero de factura', 'class': 'form-control', }),
            'provider': forms.Select(attrs={'class': 'custom-select select2',}),
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'value': datetime.now().strftime('%Y-%m-%d'), 'autocomplete': 'off', 'class': 'form-control datetimepicker-input', 'id': 'date', 'data-target': '#date', 'data-toggle': 'datetimepicker' }),
            'iva': forms.TextInput(attrs={'class': 'form-control', }),
            'subtotal': forms.TextInput(attrs={'readonly': True, 'class': 'form-control', }),
            'discount_total': forms.NumberInput(attrs={ 'class': 'form-control', }),
            'total': forms.TextInput(attrs={'readonly': True, 'class': 'form-control', }),
            'type_payment': forms.Select(attrs={'class': 'form-control', }),
            'days_to_pay': forms.NumberInput(attrs={'value': 0, 'class': 'form-control', }),
            'down_payment': forms.TextInput(attrs={'value': 0, 'class': 'form-control', }),
            'observation' : forms.TextInput(attrs={'class': 'form-control'}),
        }

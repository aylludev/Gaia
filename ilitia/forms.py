from django import forms
from django.forms import ModelForm
from datetime import datetime
from ilitia.models import Client, Sale

class ClientForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['names'].widget.attrs['autofocus'] = True

    class Meta:
        model = Client
        fields = '__all__'
        widgets = {
            'names': forms.TextInput(attrs={'placeholder': 'Ingrese sus nombres',}),
            'surnames': forms.TextInput(attrs={'placeholder': 'Ingrese sus apellidos',}),
            'dni': forms.TextInput(attrs={'placeholder': 'Ingrese su dni',}),
            'email': forms.TextInput(attrs={'placeholder': 'Ingrese su email',}),
            'date_birthday': forms.DateInput(format='%Y-%m-%d', attrs={'value': datetime.now().strftime('%Y-%m-%d'), 'autocomplete': 'off', 'class': 'form-control datetimepicker-input datetimepiker4', 'id': 'date_joined', 'data-target': '#date_joined', 'data-toggle': 'datetimepicker' }),
            'address': forms.TextInput(attrs={'placeholder': 'Ingrese su dirección', }),
            'gender': forms.Select(),
            'observation': forms.TextInput(attrs={'placeholder': 'Observaciones',}),
        }
        exclude = ['created_at', 'updated_at', 'created_by', 'updated_by']

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

class SaleForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cli'].queryset = Client.objects.none()

    class Meta:
        model = Sale
        fields = '__all__'
        widgets = {
            'cli': forms.Select(attrs={'class': 'custom-select select2',}),
            'invoice_number': forms.TextInput(attrs={'readonly': True, 'class': 'form-control', }),
            'iva': forms.TextInput(attrs={'class': 'form-control', }),
            'subtotal': forms.TextInput(attrs={'readonly': True, 'class': 'form-control', }),
            'discountall': forms.TextInput(attrs={ 'class': 'form-control', }),
            'total': forms.TextInput(attrs={'readonly': True, 'class': 'form-control', }),
            'type_payment': forms.Select(attrs={'class': 'form-control', }),
            'days_to_pay': forms.NumberInput(attrs={'value': 0, 'class': 'form-control', }),
            'down_payment': forms.NumberInput(attrs={'value': 0.00, 'class': 'form-control', }),
            'observation' : forms.TextInput(attrs={'class': 'form-control'}),
        }


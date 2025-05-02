from django.db import models
from django.forms import model_to_dict
from ilitia.choices import GENDER
from artemisa.models import Product
from datetime import datetime
from hades.models import BaseModel

class Client(BaseModel):
    names = models.CharField(max_length=150, verbose_name='Nombres')
    last_names = models.CharField(max_length=150, verbose_name='Apellidos')
    dni = models.CharField(max_length=10, unique=True, null=True, blank=True, verbose_name='Cedula')
    email = models.EmailField(max_length=254, null=True, blank=True, unique=True, verbose_name='Correo electrónico')
    address = models.CharField(max_length=150, null=True, blank=True, verbose_name='Dirección')
    city = models.CharField(max_length=150, null=True, blank=True, verbose_name='Ciudad')
    cellphone = models.CharField(max_length=150, null=True, blank=True, verbose_name='Telefono')
    gender = models.CharField(max_length=10, choices=GENDER, default='male', verbose_name='Sexo')
    observation = models.CharField(max_length=254, null=True, blank=True, verbose_name='Observaciones')

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        return '{} {} / {}'.format(self.names, self.last_names, self.dni)

    def to_json(self):
        item = model_to_dict(self)
        item['gender'] = {'id': self.gender, 'name': self.get_gender_display()}
        item['full_name'] = self.get_full_name()
        return item

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['id']

class Sale(BaseModel):
    TYPE_PAYMENT = [
        ('CREDIT', 'Crédito'),
        ('CASH', 'Contado'),
    ]

    cli = models.ForeignKey(Client, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(default=datetime.now)
    invoice_number = models.CharField(max_length=50, blank=True, null=True)
    subtotal = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    iva = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    discountall = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    total = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    type_payment = models.CharField(max_length=10, choices=TYPE_PAYMENT, default='CREDIT')
    down_payment = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    days_to_pay = models.IntegerField(default=0)
    observation = models.CharField(max_length=254, null=True, blank=True)

    def __str__(self):
        return self.cli.names

    def to_json(self):
        item = model_to_dict(self)
        item['cli'] = self.cli.to_json()
        item['invoice_number'] = self.invoice_number
        item['subtotal'] = format(self.subtotal, '.2f')
        item['iva'] = format(self.iva, '.2f')
        item['total'] = format(self.total, '.2f')
        item['discountall'] = format(self.discountall, '.2f')
        item['date_joined'] = self.date_joined.strftime('%Y-%m-%d %H:%M')
        item['type_payment'] = self.type_payment
        item['down_payment'] = format(self.down_payment, '.2f')
        item['days_to_pay'] = format(self.days_to_pay, '.2f')
        item['det'] = [i.to_json() for i in self.detsale_set.all()]
        return item

    def delete(self, using=None, keep_parents=False):
        for det in self.detsale_set.all():
            det.prod.stock += det.cant
            det.prod.save()
        super(Sale, self).delete()

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['date_joined']

class DetSale(BaseModel):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    prod = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    cant = models.IntegerField(0)
    discount = models.IntegerField(0)
    subtotal = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)

    def __str__(self):
        return self.prod.name

    def to_json(self):
        item = model_to_dict(self, exclude=['sale'])
        item['prod'] = self.prod.to_json()
        item['price'] = format(self.price, '.2f')
        item['subtotal'] = format(self.subtotal, '.2f')
        return item

    class Meta:
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalle de Ventas'
        ordering = ['id']

# Modelo de Cotización
class Cotization(BaseModel):
    TYPE_PAYMENT = [
        ('CREDIT', 'Crédito'),
        ('CASH', 'Contado'),
    ]

    date_joined = models.DateField(default=datetime.now)
    subtotal = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    iva = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    discountall = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    total = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    type_payment = models.CharField(max_length=10, choices=TYPE_PAYMENT, default='CASH')
    down_payment = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    observation = models.CharField(max_length=254, null=True, blank=True)

    def __str__(self):
        return self.date_joined.strftime('%Y-%m-%d')

    def toJSON(self):
        item = model_to_dict(self)
        item['subtotal'] = format(self.subtotal, '.2f')
        item['iva'] = format(self.iva, '.2f')
        item['total'] = format(self.total, '.2f')
        item['discountall'] = format(self.discountall, '.2f')
        item['date_joined'] = self.date_joined.strftime('%Y-%m-%d')
        item['type_payment'] = self.type_payment
        item['down_payment'] = format(self.down_payment, '.2f')
        item['det'] = [i.to_json() for i in self.detcotization_set.all()]
        return item

    def delete(self, using=None, keep_parents=False):
        for det in self.detcotization_set.all():
            det.prod.stock += det.cant
            det.prod.save()
        super(Cotization, self).delete()

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        ordering = ['date_joined']

class CotizationDetail(BaseModel):
    cotization = models.ForeignKey(Sale, on_delete=models.CASCADE)
    prod = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    cant = models.IntegerField(0)
    discount = models.IntegerField(0)
    subtotal = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)

    def __str__(self):
        return self.prod.name

    def to_json(self):
        item = model_to_dict(self, exclude=['cotization'])
        item['prod'] = self.prod.to_json()
        item['price'] = format(self.price, '.2f')
        item['subtotal'] = format(self.subtotal, '.2f')
        return item

    class Meta:
        verbose_name = 'Detalle de Cotización'
        verbose_name_plural = 'Detalle de Cotizaciones'
        ordering = ['id']

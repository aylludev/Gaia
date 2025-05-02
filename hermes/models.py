from django.db import models
from django.forms import model_to_dict
from hades.models import BaseModel
from ilitia.models import Sale
from artemisa.models import Purchase
from datetime import datetime

# Create your models here.
class PurchasePayment(BaseModel):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='payments')
    invoice = models.CharField(max_length=50, blank=True, null=True)
    days_to_expiration = models.IntegerField(default=0)
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.TextField(blank=True, null=True)

    def to_json(self):
        item = model_to_dict(self)
        item['purchase'] = self.purchase.to_json()
        item['payment_date'] = self.payment_date.strftime('%Y-%m-%d')
        item['amount'] = format(self.amount, '.2f')
        return item
    
    class Meta:
        verbose_name = 'Pago de Compra'
        verbose_name_plural = 'Pagos de Compras'
        ordering = ['payment_date']

# Pagos de Ventas
class SalePayment(BaseModel):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    invoice = models.CharField(max_length=50, blank=True, null=True)
    days_to_expiration = models.IntegerField(default=0)
    payment_date = models.DateTimeField(default=datetime.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.TextField(blank=True, null=True)

    def to_json(self):
        item = model_to_dict(self)
        item['sale'] = self.sale.to_json()
        item['payment_date'] = self.payment_date.strftime('%Y-%m-%d %H:%M:%S')
        item['amount'] = format(self.amount, '.2f')
        return item
    
    class Meta:
        verbose_name = 'Pagos de Venta'
        verbose_name_plural = 'Pagos de Ventas'
        ordering = ['payment_date']

class CashClosing(BaseModel):
    last_login = models.DateTimeField()
    date = models.DateTimeField(default=datetime.now)
    total_cash = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    observations = models.TextField(blank=True, null=True)

    def to_json(self):
        item = model_to_dict(self)
        item['created_at'] = self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        item['updated_at'] = self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        item['last_login'] = self.last_login.strftime('%Y-%m-%d %H:%M:%S')
        item['date'] = self.date.strftime('%Y-%m-%d %H:%M:%S')
        item['total_cash'] = format(self.total_cash, '.2f')
        return item

    class Meta:
        verbose_name = "Cierre de Caja"
        verbose_name_plural = "Cierres de Caja"
        ordering = ['-date']
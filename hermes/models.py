from django.db import models
from django.forms import model_to_dict
from hades.models import BaseModel
from artemisa.models import Purchase

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
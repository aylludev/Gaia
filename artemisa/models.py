# artemisa/models.py
from django.db import models
from django.forms import model_to_dict
from datetime import datetime

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    tax_id = models.CharField(max_length=20)  # NIT
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def to_json(self):
        item = model_to_dict(self)
        item['id'] = self.id
        return item
    
    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['id']

class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)
    desc = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name

    def to_json(self):
        item = model_to_dict(self)
        return item

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['id']

class Product(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    cat = models.ForeignKey(Category, on_delete=models.CASCADE)
    unit = models.CharField(max_length=50)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def last_purchase_price(self):
        detail = PurchaseDetail.objects.filter(product=self).order_by('-purchase__date').first()
        return detail.unit_price if detail else None

    def to_json(self):
        item = model_to_dict(self)
        item['cat'] = self.cat.to_json()
        item['last_purchase_price'] = float(self.last_purchase_price) if self.last_purchase_price else None
        item['stock'] = float(self.stock)
        item['sale_price'] = float(self.sale_price)
        return item

class Purchase(models.Model):
    TYPE_PAYMENT = [
        ('CREDIT', 'Crédito'),
        ('CASH', 'Contado'),
    ]

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    date_joined = models.DateField(default=datetime.now)
    subtotal = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    iva = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    discountall = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    total = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    type_payment = models.CharField(max_length=10, choices=TYPE_PAYMENT, default='CREDIT')
    down_payment = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    observation = models.CharField(max_length=254, null=True, blank=True)

    def __str__(self):
        return self.supplier.names

    def toJSON(self):
        item = model_to_dict(self)
        item['supplier'] = self.supplier.to_json()
        item['subtotal'] = format(self.subtotal, '.2f')
        item['iva'] = format(self.iva, '.2f')
        item['total'] = format(self.total, '.2f')
        item['discountall'] = format(self.discountall, '.2f')
        item['date_joined'] = self.date_joined.strftime('%Y-%m-%d')
        item['type_payment'] = self.type_payment
        item['down_payment'] = format(self.down_payment, '.2f')
        item['det'] = [i.to_json() for i in self.purchasedetail_set.all()]
        return item

    def delete(self, using=None, keep_parents=False):
        for det in self.purchasedetail_set.all():
            det.prod.stock += det.cant
            det.prod.save()
        super(Purchase, self).delete()

    class Meta:
        verbose_name = 'Compras'
        verbose_name_plural = 'Compras'
        ordering = ['date_joined']

class PurchaseDetail(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    cant = models.IntegerField(0)
    discount = models.IntegerField(0)
    subtotal = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)

    def __str__(self):
        return self.product.name

    def to_json(self):
        item = model_to_dict(self, exclude=['sale'])
        item['prod'] = self.product.to_json()
        item['price'] = format(self.price, '.2f')
        item['subtotal'] = format(self.subtotal, '.2f')
        return item

    class Meta:
        verbose_name = 'Detalle de la Compra'
        verbose_name_plural = 'Detalle de la Compra'
        ordering = ['id']

class CreditPurchase(models.Model):
    purchase = models.OneToOneField(Purchase, on_delete=models.CASCADE, related_name="credit_purchase")
    total_credit = models.DecimalField(max_digits=10, decimal_places=2)
    down_payment = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pendiente'), ('paid', 'Pagado')], default='pending')

    def total_paid(self):
        """Calcula el saldo pendiente del crédito."""
        total_paid = self.down_payment + sum(self.payments.values_list('amount', flat=True))
        return total_paid
    
    def to_json(self):
        item = model_to_dict(self, exclude=['sale'])
        item['names'] = self.purchase.cli.names
        item['lastnames'] = self.purchase.purchase.surnames,
        item['date_joined'] = self.purchase.date_joined.strftime('%Y-%m-%d')
        item['total_credit'] = float(self.total_credit)
        item['total_paid'] = float(self.total_paid())
        item['pending_balance'] = float(self.total_credit - self.total_paid())
        return item

    def __str__(self):
        return f"Crédito #{self.sale.id} - {self.sale.cli}"

class CreditPayment(models.Model):
    credit_sale = models.ForeignKey(CreditPurchase, on_delete=models.CASCADE, related_name="payments")
    date = models.DateTimeField(default=datetime.now, verbose_name="Fecha de pago")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Abono")

    def __str__(self):
        return f"Pago de ${self.amount} - {self.credit_sale.purchase.cli} - {self.date}"
    
    def to_json(self):
        return {
            "id": self.id,
            "credit_sale": self.credit_sale.to_json(),
            "date": self.date.isoformat(),
            "amount": float(self.amount),
        }

class InventoryEntry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=100, default="Purchase")

    def to_json(self):
        return {
            "id": self.id,
            "product": self.product.to_json(),
            "quantity": float(self.quantity),
            "date": self.date.isoformat(),
            "reason": self.reason,
        }

class InventoryExit(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=100, default="Sale or internal use")

    def to_json(self):
        return {
            "id": self.id,
            "product": self.product.to_json(),
            "quantity": float(self.quantity),
            "date": self.date.isoformat(),
            "reason": self.reason,
        }

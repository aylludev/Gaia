# artemisa/models.py
from django.db import models
from django.forms import model_to_dict
from hades.models import BaseModel
from artemisa.choices import *
from django.utils import timezone

class Category(BaseModel):
    name = models.CharField(max_length=150, unique=True)
    desc = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name

    def to_json(self):
        item = model_to_dict(self)
        item['created_at'] = self.created_at.strftime('%Y-%m-%d')
        item['updated_at'] = self.updated_at.strftime('%Y-%m-%d')
        return item

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['id']

class UnitMeasure(BaseModel):
    quantity = models.DecimalField(max_digits=10, decimal_places=0)
    unit = models.CharField(max_length=50, choices=UNIT_MEASURE_CHOICES)

    def __str__(self):
        return f"{self.quantity} {self.unit}"
    
    def to_json(self):
        item = model_to_dict(self)
        item['quantity'] = format(self.quantity)
        item['created_at'] = self.created_at.strftime('%Y-%m-%d')
        item['updated_at'] = self.updated_at.strftime('%Y-%m-%d')
        item['full_name'] = f"{self.quantity} {self.unit}"
        return item

class Product(BaseModel):
    code = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name='Código')
    name = models.CharField(max_length=100, verbose_name='Nombre')
    cat = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Categoria')
    unit = models.ForeignKey(UnitMeasure, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Unidad de medida')
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Stock')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Precio de compra')
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Precio de venta')

    def __str__(self):
        return f"{self.name} ({self.unit})"
    
    @property
    def last_purchase_price(self):
        detail = PriceHistory.objects.filter(product=self).order_by('-effective_date').first()
        return detail if detail else None

    def to_json(self):
        item = model_to_dict(self)
        item['name'] = self.__str__()
        item['cat'] = self.cat.to_json()
        item['stock'] = format(self.stock, '.0f')
        item['sale_price'] = format(self.sale_price, '.0f')
        item['purchase_price'] = format(self.purchase_price, '.0f')
        item['value'] = format(self.stock * self.purchase_price, '.0f')
        item['unit'] = self.unit.to_json()
        return item

class PriceHistory(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_history')
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    effective_date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-effective_date']

    def __str__(self):
        return f'{self.product.name} - Compra: {self.purchase_price}, Venta: {self.sale_price}'
    
    def to_json(self):
        item = model_to_dict(self)
        item['product'] = self.product.to_json()
        item['purchase_price'] = format(self.purchase_price, '%.2f')
        item['sale_price'] = format(self.sale_price, '%.2f')
        item['effective_date'] = self.effective_date.strftime('%Y-%m-%d')
        return item

class InventoryMovement(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=10, choices=[('entry', 'Entrada'), ('output', 'Salida'),])
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True, null=True, choices=[('purchase', 'Compra'), ('sale', 'Venta'), ('adjustment', 'Ajuste')])

    def to_json(self):
        item = model_to_dict(self)
        item['product'] = self.product.to_json()
        item['quantity'] = float(self.quantity)
        item['date'] = self.date.strftime('%Y-%m-%d')
        return item

class InventoryLog(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=[('entry', 'Entrada'), ('output', 'Salida')])
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    source_id = models.PositiveIntegerField(null=True, blank=True)  # ID de StockEntry o StockOutput

    def to_json(self):
        item = model_to_dict(self)
        item['product'] = self.product.to_json()
        item['quantity'] = float(self.quantity)
        item['date'] = self.date.strftime('%Y-%m-%d')
        return item

# Modelo Proveedor
class Provider(BaseModel):
    names = models.CharField(max_length=150, verbose_name='Nombres')
    dni = models.CharField(max_length=10, unique=True, verbose_name='NIT')
    email = models.EmailField(max_length=254, null=True, blank=True, unique=True, verbose_name='Correo electrónico')
    address = models.CharField(max_length=150, null=True, blank=True, verbose_name='Dirección')
    city = models.CharField(max_length=150, null=True, blank=True, verbose_name='Ciudad')
    cellphone = models.CharField(max_length=150, null=True, blank=True, verbose_name='Telefono')
    observation = models.CharField(max_length=254, null=True, blank=True, verbose_name='Observaciones')

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        return '{} / {}'.format(self.names, self.dni)

    def to_json(self):
        item = model_to_dict(self)
        item['full_name'] = self.get_full_name()
        return item

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['id']

# Modelo Compra
class Purchase(BaseModel):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, verbose_name='Proveedor')
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name='Numero de factura', null=True, blank=True)
    date = models.DateField(verbose_name='Fecha')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Subtotal')
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='IVA')
    discount_total = models.DecimalField(default=0.00, max_digits=9, decimal_places=2, verbose_name='Descuento')
    total = models.DecimalField(default=0.00, max_digits=9, decimal_places=2, verbose_name='Total')
    type_payment = models.CharField(max_length=10, choices=TYPE_PAYMENT, default='CREDIT')
    down_payment = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    observation = models.CharField(max_length=254, null=True, blank=True, verbose_name='Observaciones')

    def __str__(self):
        return f"{self.provider} ({self.date})"

    def to_json(self):
        item = model_to_dict(self)
        item['provider'] = self.provider.to_json()
        item['invoice_number'] = self.invoice_number
        item['subtotal'] = format(self.subtotal, '.2f')
        item['iva'] = format(self.iva, '.2f')
        item['total'] = format(self.total, '.2f')
        item['discount_total'] = format(self.discount_total, '.2f')
        item['date'] = self.date.strftime('%Y-%m-%d')
        item['type_payment'] = self.type_payment
        item['down_payment'] = format(self.down_payment, '.2f')
        item['det'] = [i.to_json() for i in self.purchasedetail_set.all()]
        return item

    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        ordering = ['date']

class PurchaseDetail(BaseModel):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, verbose_name='Compra')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Producto')
    price = models.DecimalField(default=0.00, max_digits=9, decimal_places=2, verbose_name='Precio')
    cant = models.IntegerField(default=0, verbose_name='Cantidad')
    discount = models.IntegerField(default=0, verbose_name='Descuento')
    subtotal = models.DecimalField(default=0.00, max_digits=9, decimal_places=2, verbose_name='Subtotal')

    def __str__(self):
        return self.product.name
    
    def to_json(self):
        item = model_to_dict(self, exclude=['purchase'])
        item['prod'] = self.product.to_json()
        item['price'] = format(self.price, '.2f')
        item['subtotal'] = format(self.subtotal, '.2f')
        return item
    
    class Meta:
        verbose_name = 'Detalle de la Compra'
        verbose_name_plural = 'Detalles de la Compra'
        ordering = ['id']

class PurchasePayment(BaseModel):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=50)  # Ej: efectivo, transferencia, etc.
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

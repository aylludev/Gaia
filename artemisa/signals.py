# artemisa/signals.py

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Product, PriceHistory

@receiver(pre_save, sender=Product)
def create_price_history(sender, instance, **kwargs):
    if instance.pk:
        old_product = Product.objects.get(pk=instance.pk)

        if (old_product.purchase_price != instance.purchase_price or
            old_product.sale_price != instance.sale_price):
            PriceHistory.objects.create(
                created_by=instance.created_by,
                product=instance,
                purchase_price=old_product.purchase_price,
                sale_price=old_product.sale_price
            )

# Generated by Django 5.2 on 2025-04-29 18:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('artemisa', '0012_alter_purchase_type_payment_delete_purchasepayment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='purchase',
            options={'ordering': ['-id'], 'verbose_name': 'Compra', 'verbose_name_plural': 'Compras'},
        ),
    ]

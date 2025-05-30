# Generated by Django 5.1.3 on 2025-01-22 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eapp', '0010_alter_order_payment_method_alter_order_total_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='quantity',
            field=models.IntegerField(default=1),
        ),
    ]

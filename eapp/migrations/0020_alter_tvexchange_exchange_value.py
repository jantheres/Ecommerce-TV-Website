# Generated by Django 5.1.3 on 2025-02-21 06:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eapp', '0019_tvexchange_exchangepickup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tvexchange',
            name='exchange_value',
            field=models.DecimalField(blank=True, decimal_places=2, editable=False, max_digits=10, null=True),
        ),
    ]

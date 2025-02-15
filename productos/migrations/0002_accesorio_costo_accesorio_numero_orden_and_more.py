# Generated by Django 5.1.4 on 2025-02-15 00:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='accesorio',
            name='costo',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Costo (USD)'),
        ),
        migrations.AddField(
            model_name='accesorio',
            name='numero_orden',
            field=models.DateField(blank=True, null=True, verbose_name='N° de Orden'),
        ),
        migrations.AddField(
            model_name='accesorio',
            name='proveedor',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Proveedor'),
        ),
        migrations.AddField(
            model_name='iphone',
            name='costo',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Costo (USD)'),
        ),
        migrations.AddField(
            model_name='iphone',
            name='numero_orden',
            field=models.DateField(blank=True, null=True, verbose_name='N° de Orden'),
        ),
        migrations.AddField(
            model_name='iphone',
            name='proveedor',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Proveedor'),
        ),
        migrations.AddField(
            model_name='mac',
            name='costo',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Costo (USD)'),
        ),
        migrations.AddField(
            model_name='mac',
            name='numero_orden',
            field=models.DateField(blank=True, null=True, verbose_name='N° de Orden'),
        ),
        migrations.AddField(
            model_name='mac',
            name='proveedor',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Proveedor'),
        ),
    ]

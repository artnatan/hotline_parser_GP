# Generated by Django 4.2.21 on 2025-06-04 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('brand', models.CharField(max_length=100)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('shop_name', models.CharField(max_length=255)),
                ('shop_url', models.URLField()),
                ('hotline_url', models.URLField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]

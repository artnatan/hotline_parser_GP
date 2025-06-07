from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop_name', 'price', 'updated_at')
    search_fields = ('name', 'shop_name')

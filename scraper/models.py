from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=100, default="")  # ✅ добавляем это поле
    brand = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    shop_name = models.CharField(max_length=255)
    shop_url = models.URLField()
    hotline_url = models.URLField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.brand} | {self.name} | {self.shop_name}"

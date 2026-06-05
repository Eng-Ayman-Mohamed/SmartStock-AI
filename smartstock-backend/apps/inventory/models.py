from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SKU(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='skus')
    code = models.CharField(max_length=50, unique=True)
    attributes = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.code}"


class StockLevel(models.Model):
    sku = models.OneToOneField(SKU, on_delete=models.CASCADE, related_name='stock_level')
    quantity = models.IntegerField(default=0)
    reorder_point = models.IntegerField(default=10)
    reorder_quantity = models.IntegerField(default=50)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sku.code}: {self.quantity}"


class SalesRecord(models.Model):
    """Historical daily sales data per SKU — used as training data for Prophet."""
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE, related_name='sales_records')
    date = models.DateField()
    quantity_sold = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['sku', 'date']),
        ]
        unique_together = [('sku', 'date')]

    def __str__(self):
        return f"{self.sku.code} on {self.date}: {self.quantity_sold}"

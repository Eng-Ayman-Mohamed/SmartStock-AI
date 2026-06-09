from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products',
    )
    supplier = models.ForeignKey(
        'Supplier', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products',
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit_of_measure = models.CharField(max_length=50, blank=True, default='units')
    reorder_point = models.IntegerField(default=10)
    safety_stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
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
    quantity_on_hand = models.IntegerField(default=0)
    quantity_reserved = models.IntegerField(default=0)
    reorder_point = models.IntegerField(default=10)
    reorder_quantity = models.IntegerField(default=50)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def quantity_available(self):
        return self.quantity_on_hand - self.quantity_reserved

    def __str__(self):
        return f"{self.sku.code}: {self.quantity_on_hand}"


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

class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    default_lead_time_days = models.IntegerField(default=7)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
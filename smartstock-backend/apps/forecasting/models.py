from django.db import models


class ForecastResult(models.Model):
    sku = models.ForeignKey('inventory.SKU', on_delete=models.CASCADE, related_name='forecasts')
    forecast_date = models.DateField()
    predicted_quantity = models.FloatField()
    lower_bound = models.FloatField(null=True, blank=True)
    upper_bound = models.FloatField(null=True, blank=True)
    mae = models.FloatField(null=True, blank=True)
    mape = models.FloatField(null=True, blank=True)
    model_version = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['sku', 'forecast_date']),
        ]
        unique_together = [('sku', 'forecast_date')]

    def __str__(self):
        return f'{self.sku.code} - {self.forecast_date}: {self.predicted_quantity}'


class ReorderFlag(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        CONSUMED = 'consumed', 'Consumed'
        DISMISSED = 'dismissed', 'Dismissed'

    sku = models.ForeignKey('inventory.SKU', on_delete=models.CASCADE, related_name='reorder_flags')
    quantity_available = models.IntegerField()
    total_predicted_demand = models.FloatField()
    safety_stock = models.IntegerField(default=0)
    lead_time_days = models.IntegerField(default=7)
    forecast_days = models.IntegerField(default=7)
    reorder_required = models.BooleanField(default=True)
    has_open_po = models.BooleanField(default=False)
    open_po_id = models.IntegerField(null=True, blank=True)
    reasoning = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['sku', 'status']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sku.code}: {self.status}'

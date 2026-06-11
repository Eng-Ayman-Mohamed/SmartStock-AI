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

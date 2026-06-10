from django.contrib import admin

from .models import SKU, Product, SalesRecord, StockLevel

admin.site.register(Product)
admin.site.register(SKU)
admin.site.register(StockLevel)
admin.site.register(SalesRecord)

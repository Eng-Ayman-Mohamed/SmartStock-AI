from django.contrib import admin
from .models import Product, SKU, StockLevel, SalesRecord

admin.site.register(Product)
admin.site.register(SKU)
admin.site.register(StockLevel)
admin.site.register(SalesRecord)

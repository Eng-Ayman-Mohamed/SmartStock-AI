from django.contrib import admin

from apps.inventory.models import Supplier

from .models import PurchaseOrder

admin.site.register(PurchaseOrder)
admin.site.register(Supplier)

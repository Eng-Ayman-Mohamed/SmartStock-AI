from django.contrib import admin
from .models import PurchaseOrder, Supplier

admin.site.register(PurchaseOrder)
admin.site.register(Supplier)

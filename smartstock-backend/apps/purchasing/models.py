from django.db import models


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING_APPROVAL = 'pending_approval', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        SENT = 'sent', 'Sent'
        CONFIRMED = 'confirmed', 'Confirmed'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'

    sku = models.ForeignKey('inventory.SKU', on_delete=models.CASCADE, related_name='purchase_orders')
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.CASCADE, related_name='purchase_orders')
    quantity = models.IntegerField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    requested_by = models.ForeignKey(
        'authentication.CustomUser', on_delete=models.SET_NULL, null=True, related_name='purchase_orders'
    )
    approved_by = models.ForeignKey(
        'authentication.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_orders'
    )
    agent_reasoning = models.TextField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'PO-{self.id}: {self.sku.code} x{self.quantity}'

from django.db import models


class PurchaseOrderWorkflow(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_APPROVAL = "pending_approval", "Pending Approval"
        APPROVED = "approved", "Approved"
        EMAIL_SENT = "email_sent", "Email Sent"
        WAITING_CONFIRMATION = "waiting_confirmation", "Waiting Confirmation"
        CONFIRMED = "confirmed", "Confirmed"
        REJECTED = "rejected", "Rejected"
        FAILED = "failed", "Failed"
        TIMEOUT = "timeout", "Timeout"

    purchase_order = models.OneToOneField(
        "purchasing.PurchaseOrder",
        on_delete=models.CASCADE,
        related_name="workflow",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    message_id = models.CharField(max_length=255, blank=True, null=True)
    polling_attempts = models.IntegerField(default=0)
    last_poll_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Workflow for PO-{self.purchase_order_id}: {self.status}"

    class Meta:
        ordering = ["-created_at"]

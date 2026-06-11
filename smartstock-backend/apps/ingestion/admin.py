from django.contrib import admin

from .models import Document, DocumentChunk, InvoiceScan

admin.site.register(Document)
admin.site.register(DocumentChunk)
admin.site.register(InvoiceScan)

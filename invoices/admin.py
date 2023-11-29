from django.contrib import admin
from .models import Invoice, InvoicePayment, InvoiceItem
# Register your models here.
admin.site.register(Invoice)
admin.site.register(InvoicePayment)
admin.site.register(InvoiceItem)

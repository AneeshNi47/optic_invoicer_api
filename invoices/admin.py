from django.contrib import admin
from .models import Invoice, InvoicePayment
# Register your models here.
admin.site.register(Invoice)
admin.site.register(InvoicePayment)

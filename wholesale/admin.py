from django.contrib import admin
from .models import WholeSaleVendor, WholeSaleInventory, WholeSaleOrder, WholeSaleClient, SalesOrderItems

admin.site.register(WholeSaleVendor)
admin.site.register(WholeSaleClient)
admin.site.register(WholeSaleInventory)
admin.site.register(WholeSaleOrder)
admin.site.register(SalesOrderItems)

from django.contrib import admin
from .models import Inventory, InventoryCSV

admin.site.register(Inventory)
admin.site.register(InventoryCSV)
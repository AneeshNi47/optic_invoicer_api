from django.db import models
from django.conf import settings
import random
from datetime import datetime


class Inventory(models.Model):
    SKU = models.CharField(max_length=255, unique=True, verbose_name="Stock Keeping Unit", blank=True, null=True)
    store_sku = models.CharField(max_length=255, verbose_name="Store SKU", blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    qty = models.PositiveIntegerField(default=0, verbose_name="Quantity")
    sale_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sale Value")
    cost_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cost Value")
    ITEM_TYPE_CHOICES = [
        ("Lens", "Lens"),
        ("Frames", "Frames"),
        ("Other", "Other")
    ]
    item_type = models.CharField(max_length=15, choices=ITEM_TYPE_CHOICES, default="Lens")
    brand = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    TYPE_CHOICES = [
        ("Frames", "Frames"),
        ("Lens", "Lens"),
        ("Others", "Others")
    ]
    item_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="Frames")

    
    # Default fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="inventories_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="inventories_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name="inventories")

    def generate_sku(self):
        prefix = self.organization.name[:4].upper()
        existing_skus = Inventory.objects.filter(SKU__startswith=prefix).count()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')  # Year, month, day, hour, minute, second, microsecond
        random_value = random.randint(100, 999)  # A random 3-digit number
        new_sku = f"{prefix}{existing_skus + 1:05}{timestamp}{random_value}"  # Combines count, timestamp, and random value
        return new_sku

    def save(self, *args, **kwargs):
        if not self.SKU:
            self.SKU = self.generate_sku()
        super(Inventory, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.SKU} {self.item_type} {self.store_sku}'
        return f'{self.name} {self.item_type} {self.store_sku}'

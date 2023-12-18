from django.db import models
from django.conf import settings
import random
from datetime import datetime
from organizations.models import Organization
from .tasks import download_and_process_file


class Inventory(models.Model):
    SKU = models.CharField(max_length=255, unique=True, verbose_name="Stock Keeping Unit", blank=True, null=True)
    store_sku = models.CharField(max_length=255, verbose_name="Store SKU", blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    qty = models.PositiveIntegerField(default=0, verbose_name="Quantity")
    sale_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sale Value")
    cost_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cost Value")
    brand = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    TYPE_CHOICES = [
        ("Frames", "Frames"),
        ("Lens", "Lens"),
        ("Others", "Others")
    ]
    item_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="Frames")
    STATUS_CHOICES = [
        ("Stocked", "Stocked"),
        ("Out of Stock", "Out of Stock"),
        ("Others", "Others")
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Stocked")

    
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
        is_new = self._state.adding 
        if self.qty > 0:
            self.status="Stocked"
        if not self.SKU:
            self.SKU = self.generate_sku()
        super(Inventory, self).save(*args, **kwargs)
        if is_new:
            Organization.objects.filter(id=self.organization_id).update(total_inventory=models.F('total_inventory') + 1)

    def __str__(self):
        return f'{self.item_type} -{self.store_sku} :  {self.id} - {self.qty}'


class InventoryCSV(models.Model):
    STATUS_CHOICES = [
        ("Created", "Created"),
        ("Processing", "Processing"),
        ("Completed", "Completed"),
        ("Error", "Error")
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Created")
    remarks = models.CharField(max_length=1024,blank=True, null=True)
    csv_file = models.FileField(upload_to='organization_csv/', blank=True, null=True)

    
    # Default fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="inventories_csv_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="inventories_csv_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name="inventories_csv")


    def __str__(self):
        return f'{self.csv_file} - {self.status} - {self.organization}'
    
    def save(self, *args, **kwargs):
        # Call the real save method
        super(InventoryCSV, self).save(*args, **kwargs)
        is_new = self._state.adding

        if not self.csv_file:
            print("No CSV File found")

        # Trigger the Celery task after the instance is saved
        if self.csv_file and is_new:
            download_and_process_file(self.pk)
        
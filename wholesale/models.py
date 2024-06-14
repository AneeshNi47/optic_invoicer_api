from django.db import models
from django.conf import settings
from datetime import datetime
from .choices import PAYMENT_STATUS_CHOICES, ORDER_STATUS_CHOICES

# Create your models here.

class WholeSaleVendor(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=100)
    email = models.EmailField()
    website = models.URLField()
    contact_person = models.CharField(max_length=100)
    contact_person_phone = models.CharField(max_length=100)
    contact_person_email = models.EmailField()
    contact_person_designation=models.CharField(max_length=100)
    
    # Default fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="wholesale_vendor_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="wholesale_vendor_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name="wholesale_vendor")

    
    def __str__(self):
        return self.name

class WholeSaleInventory(models.Model):
    item_code = models.CharField(max_length=100)
    item_type=models.CharField(max_length=100)
    item_property=models.CharField(max_length=100)
    group=models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    item_name = models.CharField(max_length=100)
    description = models.TextField()
    brand=models.CharField(max_length=100)
    origin=models.CharField(max_length=100)
    part_model_no = models.CharField(max_length=100)
    size=models.CharField(max_length=100)
    color=models.CharField(max_length=100)
    basic_unit_of_measure=models.CharField(max_length=100)
    std_cost = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price_1 = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price_2 = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price_3 = models.DecimalField(max_digits=10, decimal_places=2)
    re_order_qty = models.IntegerField()
    min_price=models.DecimalField(max_digits=10, decimal_places=2)
    max_discount_percentage=models.DecimalField(max_digits=10, decimal_places=2)
    preferred_vendor = models.ForeignKey(WholeSaleVendor, on_delete=models.CASCADE, related_name="wholesale_inventory", null=True, blank=True) , 
    vendor_ref_no=models.CharField(max_length=100)
    
    # Default fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="wholesale_inventory_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="wholesale_inventory_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name="wholesale_inventory")

    
    def __str__(self):
        return f'{self.item_name} - {self.item_code} - {self.re_order_qty}'
    

class WholeSaleClient(models.Model):
    id_no = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    address = models.TextField()
    country=models.CharField(max_length=100)
    tax_number = models.CharField(max_length=100)
    tax_percentage = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    phone = models.CharField(max_length=100)
    email = models.EmailField()
    website = models.URLField()
    contact_person = models.CharField(max_length=100)
    contact_person_phone = models.CharField(max_length=100)
    contact_person_email = models.EmailField()
    contact_person_designation=models.CharField(max_length=100)
    total_orders = models.IntegerField(default=0)
    total_credit=models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    total_payment=models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    last_payment_date=models.DateField(null=True, blank=True)
    last_order_date=models.DateField(null=True, blank=True)
    is_active=models.BooleanField(default=True)
    
    # Default fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="wholesale_client_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="wholesale_client_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name="wholesale_client")

    
    def __str__(self):
        return f'{self.name} - {self.id_no} - {self.total_credit} - {self.total_payment}'


class WholeSaleOrder(models.Model):
    order_no = models.CharField(max_length=100, unique=True)
    order_date = models.DateField()
    is_taxable = models.BooleanField(default=True)
    client = models.ForeignKey(WholeSaleClient, on_delete=models.CASCADE, related_name="wholesale_order")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2)
    total_tax = models.DecimalField(max_digits=10, decimal_places=2)
    total_payment = models.DecimalField(max_digits=10, decimal_places=2)
    total_credit = models.DecimalField(max_digits=10, decimal_places=2)
    payment_due_date = models.DateField()
    payment_status= models.CharField(max_length=15, choices=PAYMENT_STATUS_CHOICES, default=1)
    order_status= models.CharField(max_length=15, choices=ORDER_STATUS_CHOICES, default=1)
    remarks = models.TextField()
    
    # Default fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="wholesale_order_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="wholesale_order_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name="wholesale_order")

    
    def __str__(self):
        return f'{self.order_no} - {self.order_date} - {self.payment_due_date} - {self.payment_status} - {self.order_status}'
    
    def generate_order_number(self):
            # Extract the first four characters of the organization name
        prefix = self.organization.name[:4].upper()

        # Get the current year
        year = datetime.now().year

        # Get the count of invoices for the current year and organization
        count = WholeSaleOrder.objects.filter(
            organization=self.organization,
            created_on__year=year
        ).count() + 1  # Add 1 for the current invoice
        # Return the formatted WholeSale Order number
        if self.is_taxable:
            return f"WSO{prefix}{year}{count:05}"
        else:
            return f"WSO{prefix}NT{year}{count:05}"
    

    def save(self, *args, **kwargs):
        if not self.order_no:
            self.order_no = self.generate_order_number()
        super().save(*args, **kwargs)

class SalesOrderItems(models.Model):
    order = models.ForeignKey(WholeSaleOrder, on_delete=models.CASCADE, related_name='items')
    inventory_item = models.ForeignKey(WholeSaleInventory, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    selected_selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage= models.DecimalField(max_digits=5, decimal_places=2,default=0.0)

    def __str__(self):
            return f'{self.order.order_no} - {self.inventory_item.item_name} - {self.quantity}'
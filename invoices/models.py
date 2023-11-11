from django.db import models
from uuid import uuid4
from organizations.models import Organization
from django.contrib.auth.models import User
from customers.models import Customer, Prescription
from inventory.models import Inventory
from datetime import datetime
 
class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    invoice_number = models.CharField(max_length=255, unique=True, blank=True)
    date = models.DateField(auto_now_add=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True)
    items=models.ManyToManyField(Inventory, related_name="invoice_items",null=True, blank=True,)
    remarks = models.TextField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True,default=0)
    advance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    STATUS_CHOICES = [
        ("Created", "Created"),
        ("Advanced", "Advanced"),
        ("Paid", "Paid"),
        ("Delivered", "Delivered"),
        ("Scrapped", "Scrapped"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Created")
    is_active = models.BooleanField(default=True)
    is_taxable = models.BooleanField(default=True)

    # Default fields
    created_by = models.ForeignKey(User, related_name="invoices_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, related_name="invoices_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.invoice_number} {self.customer.first_name} on {self.created_on}"


    def generate_invoice_number(self):
        # Extract the first four characters of the organization name
        prefix = self.organization.name[:4].upper()

        # Get the current year
        year = datetime.now().year

        # Get the count of invoices for the current year and organization
        count = Invoice.objects.filter(
            organization=self.organization,
            created_on__year=year
        ).count() + 1  # Add 1 for the current invoice
        # Return the formatted invoice number
        if self.is_taxable:
            return f"{prefix}{year}{count:05}"
        else:
            return f"{prefix}NT{year}{count:05}"

    def save(self, *args, **kwargs):
        # If the invoice doesn't have an invoice number, generate one
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        total_price = 0 
        for item in self.items.all():
            total_price += item.sale_value

        self.total = total_price - self.discount
        self.balance = self.total - self.advance
        super(Invoice, self).save(*args, **kwargs)
from django.db import models, transaction
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
    items=models.ManyToManyField(Inventory,related_name="inventory_items",null=True, blank=True,)
    remarks = models.TextField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True,default=0)
    advance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    PAYMENT_MODE_CHOICES = [    
        ("Cash", "Cash"),
        ("Card", "Card"),
        ("Online", "Online"),
        ("Others", "Others")
    ]
    advance_payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, default="Cash")
    tax_percentage = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True,default=5)
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
        # Flag to check if the instance is new
        is_new = self._state.adding
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super(Invoice, self).save(*args, **kwargs)

        # If the instance is new and advance is not 0, create InvoicePayment
        if is_new and self.advance != 0:
            InvoicePayment.objects.create(
                invoice=self,
                invoice_number=self.invoice_number,
                amount=self.advance,
                payment_type="Advance",
                payment_mode=self.advance_payment_mode,
                created_by=self.created_by,
                organization=self.organization
            )


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    inventory_item = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    sale_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sale Value Snapshot", default=0)
    cost_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cost Value Snapshot", default=0)
    quantity = models.IntegerField(default=1)

    class Meta:
        unique_together = ('invoice', 'inventory_item')

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.sale_value = self.inventory_item.sale_value
            self.cost_value = self.inventory_item.cost_value

        super(InvoiceItem, self).save(*args, **kwargs)
    

    def __str__(self):
        return f"{self.invoice.invoice_number} {self.inventory_item.name} > {self.quantity}"


class InvoicePayment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    invoice_number = models.CharField(max_length=255, blank=True)
    amount=models.DecimalField(max_digits=10, decimal_places=2)
    invoice=models.ForeignKey(Invoice, related_name="invoice_payment", on_delete=models.CASCADE, null=True)
    PAYMENT_TYPE_CHOICES = [
        ("Advance", "Advance"),
        ("General", "General"),
        ("Return", "Return"),
        ("Others", "Others")
    ]
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES, default="General")
    PAYMENT_MODE_CHOICES = [
        ("Cash", "Cash"),
        ("Card", "Card"),
        ("Online", "Online"),
        ("Others", "Others")
    ]
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, default="Cash")
    remarks= models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Default fields
    created_by = models.ForeignKey(User, related_name="invoice_payment_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, related_name="invoice_payment_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)


    def __str__(self):
        if self.invoice:
            return f"{self.invoice_number} {self.payment_type} > {self.amount}"
        else:
            return f"{self.invoice_number}"


    def save(self, *args, **kwargs):
        with transaction.atomic():
            # Perform validations
            self.validate_invoice()
            self.validate_payment_editing()
            self.validate_invoice_status()

            # If validations pass, proceed to save
            super(InvoicePayment, self).save(*args, **kwargs)

            # Adjust the invoice balance after saving
            self.adjust_invoice_balance()

    def validate_invoice(self):
        """ Ensure that an invoice is set for the payment. """
        if not self.invoice:
            raise ValueError("Invoice must be set for the payment")

    def validate_payment_editing(self):
        """ Prevent editing of existing active payments. """
        if self._state.adding or not InvoicePayment.objects.filter(pk=self.pk, is_active=True).exists():
            return
        if not self.is_active:
            super(InvoicePayment, self).save(update_fields=['is_active'])
        else:
            raise ValueError("Editing existing payments is not allowed")

    def validate_invoice_status(self):
        """ Check if the invoice is in a state that allows adding payments. """
        if self.invoice.status in ["Scrapped", "Paid"]:
            raise ValueError("Cannot add payment for Completed/Scrapped Invoice")

    def adjust_invoice_balance(self):
        """ Adjust the invoice balance for new payments. """
        if self.payment_type == "Advance":
            return

        total_payments = sum(payment.amount for payment in self.invoice.invoice_payment.all() if payment.payment_type != "Advance")
        self.invoice.balance = self.invoice.total - total_payments

        if self.invoice.balance < 0:
            raise ValueError("Total payments exceed the invoice amount")
        if self.invoice.balance == 0:
            self.invoice.status = "Paid"
        self.invoice.save()


    def delete(self, *args, **kwargs):
        if self.invoice.status in ["Delivered", "Scrapped"]:
            # Prevent deletion if invoice status is Delivered or Scrapped
            raise ValueError("Cannot delete payment for delivered or scrapped invoices")

        if self.is_active:
            # Mark as deleted (soft delete) and adjust the invoice balance
            self.is_active = False
            self.save(update_fields=["is_active"])
            self.invoice.balance += self.amount
            self.invoice.save()
        else:
            # If already marked as deleted, raise an exception
            raise ValueError("This payment has already been deleted")
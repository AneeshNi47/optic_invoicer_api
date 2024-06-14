from django.contrib.auth.models import User
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255)
    address_first_line = models.CharField(max_length=255)
    email = models.EmailField()
    secondary_email = models.EmailField(blank=True, null=True)
    primary_phone_mobile = models.CharField(max_length=20)
    other_contact_numbers = models.TextField(blank=True, null=True)  # Comma-separated or newline-separated numbers
    phone_landline = models.CharField(max_length=20, blank=True, null=True)
    logo = models.ImageField(upload_to='organization_logos/', blank=True, null=True)
    translation_required = models.BooleanField(default=False)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    post_box_number = models.CharField(max_length=50, blank=True, null=True)
    services = models.TextField(blank=True, null=True)  # Comma-separated or newline-separated services
    is_active = models.BooleanField(default=True)
    is_retail = models.BooleanField(default=True)
    is_wholesale = models.BooleanField(default=False)
    total_customers = models.PositiveIntegerField(default=0, verbose_name="total_customers")
    total_prescriptions = models.PositiveIntegerField(default=0, verbose_name="total_prescriptions")
    total_inventory = models.PositiveIntegerField(default=0, verbose_name="total_inventory")
    total_invoices = models.PositiveIntegerField(default=0, verbose_name="total_invoices")
    customer_statistics = models.JSONField(default=list, blank=True, null=True)
    prescription_statistics =  models.JSONField(default=list, blank=True, null=True)
    inventory_statistics =  models.JSONField(default=list, blank=True, null=True)
    invoice_statistics =  models.JSONField(default=list, blank=True, null=True)


    # Default fields
    created_by = models.ForeignKey(User, related_name="organizations_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, related_name="organizations_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, related_name="owned_organizations", on_delete=models.CASCADE)


    def __str__(self):
        return self.name


class Payment(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remarks = models.TextField(null=True, blank=True)
    PAYMENT_MODE_CHOICES = [
        ("Cash", "Cash"),
        ("Debit Card", "Debit Card"),
        ("Credit Card", "Credit Card"),
        ("Paypal", "Paypal"),
    ]
    payment_mode = models.CharField(max_length=15, choices=PAYMENT_MODE_CHOICES, default="Cash")

    # Default fields
    created_by = models.ForeignKey(User, related_name="payment_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, related_name="payment_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    

class Subscription(models.Model):
    TYPE_CHOICES = [
        ("Demo", "Demo"),
        ("Yearly", "Yearly"),
        ("Monthly", "Monthly"),
        ("Weekly", "Weekly"),
        ("Trial", "Trial"),
    ]
    subscription_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="Trial")
    STATUS_CHOICES = [
        ("Paid", "Paid"),
        ("Expired", "Expired"),
        ("Pending", "Pending"),
        ("Error", "Error"),
        ("Stopped", "Stopped"),
        ("Trial","Trial")
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Trial")
    trial_start_date = models.DateTimeField(null=True)
    trial_end_date = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
    payments = models.ManyToManyField(Payment, related_name="subscription_payments",null=True, blank=True,)

    # Default fields
    created_by = models.ForeignKey(User, related_name="subscription_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, related_name="subscription_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate other active subscriptions for the same organization
            Subscription.objects.filter(
                organization=self.organization,
                is_active=True
            ).exclude(
                id=self.id  # Exclude the current subscription if it's already in the database
            ).update(is_active=False)

        super().save(*args, **kwargs)
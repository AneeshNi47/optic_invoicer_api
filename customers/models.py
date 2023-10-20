from django.db import models
from organizations.models import Organization
from django.contrib.auth.models import User

 # Utility function to generate choices for FloatFields
def float_range(start, stop, step):
    while start < stop:
        yield round(start, 2)
        start += step

class Customer(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['phone', 'organization'], name='unique_phone_per_org'),
            models.UniqueConstraint(fields=['email', 'organization'], name='unique_email_per_org')
        ]
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    )
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    THEME_MODE_CHOICES = (
        ('L', 'Light'),
        ('D', 'Dark'),
        ('S', 'System')
    )
    theme_mode =models.CharField(max_length=1, choices=THEME_MODE_CHOICES, default='S')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='N')
    user = models.OneToOneField(User, on_delete=models.SET_NULL,related_name="customer", null=True, blank=True)  
    is_active = models.BooleanField(default=True)
    # Default fields
    created_by = models.ForeignKey(User, related_name="customer_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, related_name="customer_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.phone} {self.email}"

class Prescription(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='prescriptions')

    SPHERE_CHOICES = [(i, f"{i:.2f}") for i in list(float_range(-20.0, 20.0, 0.25))]
    CYLINDER_CHOICES = [(i, f"{i:.2f}") for i in list(float_range(-10.0, 10.0, 0.25))]
    AXIS_CHOICES = [(i, str(i)) for i in range(1, 181)]
    PRISM_CHOICES = [(i, f"{i:.2f}") for i in list(float_range(0.0, 10.0, 0.25))]  # Example range and step for PRISM
    ADD_CHOICES = [(i, f"{i:.2f}") for i in list(float_range(0.0, 4.0, 0.25))]     # Example range and step for ADD

    left_sphere = models.FloatField(choices=SPHERE_CHOICES, null=True, blank=True)
    right_sphere = models.FloatField(choices=SPHERE_CHOICES, null=True, blank=True)
    left_cylinder = models.FloatField(choices=CYLINDER_CHOICES, null=True, blank=True)
    right_cylinder = models.FloatField(choices=CYLINDER_CHOICES, null=True, blank=True)
    left_axis = models.PositiveSmallIntegerField(choices=AXIS_CHOICES, null=True, blank=True)
    right_axis = models.PositiveSmallIntegerField(choices=AXIS_CHOICES, null=True, blank=True)
    left_prism = models.FloatField(choices=PRISM_CHOICES, null=True, blank=True)
    right_prism = models.FloatField(choices=PRISM_CHOICES, null=True, blank=True)
    left_add = models.FloatField(choices=ADD_CHOICES, null=True, blank=True)
    right_add = models.FloatField(choices=ADD_CHOICES, null=True, blank=True)
    left_ipd = models.FloatField(null=True, blank=True)  # Interpupillary Distance for left eye
    right_ipd = models.FloatField(null=True, blank=True) # Interpupillary Distance for right eye
    pupillary_distance = models.FloatField(null=True, blank=True)
    additional_notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    # Default fields
    created_by = models.ForeignKey(User, related_name="prescription_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, related_name="prescription_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.customer.first_name} on {self.created_on}"

   

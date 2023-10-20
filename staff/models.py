from django.db import models
from organizations.models import Organization
from django.contrib.auth.models import User

class Staff(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff")
    staff_superuser = models.BooleanField(default=False)

    # Default fields
    created_by = models.ForeignKey(User, related_name="staff_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, related_name="staff_updated", on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)  # Assuming you want to link staff to an organization

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.designation}"


    def save(self, *args, **kwargs):
        if self.staff_superuser:
            existing_superuser = Staff.objects.filter(organization=self.organization, staff_superuser=True)
            if self.pk:  # If updating, exclude current instance
                existing_superuser = existing_superuser.exclude(pk=self.pk)
            if existing_superuser.exists():
                raise ValueError("There is already a superuser for this organization.")
        super(Staff, self).save(*args, **kwargs)
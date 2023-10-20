from django.contrib import admin
from .models import Organization, Subscription, Payment
# Register your models here.
admin.site.register(Organization)
admin.site.register(Subscription)
admin.site.register(Payment)

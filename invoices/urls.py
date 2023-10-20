from django.urls import path
from rest_framework import routers
from .api import InvoiceViewSet, CreateInvoiceView

router = routers.DefaultRouter()
router.register('api/invoice', InvoiceViewSet, 'invoices')

urlpatterns = [
    path('api/invoice/create/', CreateInvoiceView.as_view(), name='create-invoices'),
    path('api/invoice/update/', CreateInvoiceView.as_view(), name='update-invoices'),
] + router.urls

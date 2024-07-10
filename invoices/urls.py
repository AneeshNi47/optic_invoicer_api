from django.urls import path
from rest_framework import routers
from .api import InvoiceViewSet, CreateInvoiceView, InvoicePDFView, InvoicePaymentViewSet, InvoiceCustomerPDFView, GetInvoice

router = routers.DefaultRouter()
router.register('api/invoice', InvoiceViewSet, 'invoices')
router.register('api/invoice-payment', InvoicePaymentViewSet, 'invoice-payments')

urlpatterns = [
    path('api/invoice/create/', CreateInvoiceView.as_view(), name='create-invoices'),
    path('api/invoice/get', GetInvoice.as_view(), name='get-invoices'),

    path('api/invoice/update/', CreateInvoiceView.as_view(), name='update-invoices'),
    path('api/invoice/re-calculate/', CreateInvoiceView.as_view(), name='re-calculate-invoices'),
    path('api/invoice/pdf/<uuid:invoice_id>/', InvoicePDFView.as_view(), name='invoice_pdf'),
    path('api/invoice/customer-pdf/<uuid:invoice_id>/', InvoiceCustomerPDFView.as_view(), name='invoice_customer_pdf'),

] + router.urls

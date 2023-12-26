from rest_framework import routers
from django.urls import path
from .api import CustomerViewSet, CustomerSearchView, PrescriptionViewSet


router = routers.DefaultRouter()
router.register('api/customer', CustomerViewSet, 'customers')
router.register('api/prescriptions', PrescriptionViewSet, 'prescriptions')

urlpatterns = [
    path('api/search_customer', CustomerSearchView.as_view(), name='search_customer'),
] + router.urls


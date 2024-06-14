from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import WholeSaleVendorViewSet, WholeSaleInventoryViewSet, WholeSaleOrderViewSet, WholeSaleClientViewSet

router = DefaultRouter()
router.register('api/wholesale-vendors', WholeSaleVendorViewSet, 'wholesale-vendors')
router.register('api/wholesale-inventory', WholeSaleInventoryViewSet, 'wholesale-inventory')
router.register('api/wholesale-clients', WholeSaleClientViewSet, 'wholesale-client')
router.register('api/wholesale-orders', WholeSaleOrderViewSet, 'wholesale-order')

urlpatterns = [
    path('', include(router.urls)),
]

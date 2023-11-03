from rest_framework import routers
from django.urls import path
from .api import InventoryViewSet, InventorySearchView,BulkInventoryCreateView
from django.urls import path


router = routers.DefaultRouter()
router.register('api/inventory', InventoryViewSet, 'inventory')

urlpatterns = [
    path('api/search_inventory', InventorySearchView.as_view(), name='search_inventory'),
    path('api/inventory/bulk-create/', BulkInventoryCreateView.as_view(), name='bulk-inventory-create')
] + router.urls

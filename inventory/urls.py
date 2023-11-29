from rest_framework import routers
from django.urls import path
from .api import InventoryViewSet, InventorySearchView,BulkInventoryCreateView, InventoryCSVViewSet, ProcessCSVViewSet
from django.urls import path


router = routers.DefaultRouter()
router.register('api/inventory', InventoryViewSet, 'inventory')
router.register('api/inventory-csv', InventoryCSVViewSet, 'inventory-csv')

urlpatterns = [
    path('api/search_inventory', InventorySearchView.as_view(), name='search_inventory'),
    path('api/process-csv', ProcessCSVViewSet.as_view(), name='process-csv'),
    path('api/inventory/bulk-create/', BulkInventoryCreateView.as_view(), name='bulk-inventory-create')
] + router.urls

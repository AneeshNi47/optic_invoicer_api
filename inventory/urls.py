from rest_framework import routers
from django.urls import path
from .api import InventoryViewSet, InventorySearchView


router = routers.DefaultRouter()
router.register('api/inventory', InventoryViewSet, 'inventory')

urlpatterns = [
    path('api/search_inventory', InventorySearchView.as_view(), name='search_inventory'),
] + router.urls

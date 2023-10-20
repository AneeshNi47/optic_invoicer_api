from rest_framework import routers
from .api import InventoryViewSet


router = routers.DefaultRouter()
router.register('api/inventory', InventoryViewSet, 'inventory')

urlpatterns = router.urls
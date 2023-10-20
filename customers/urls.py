from rest_framework import routers
from django.urls import path
from .api import CustomerViewSet, CustomerSearchView


router = routers.DefaultRouter()
router.register('api/customer', CustomerViewSet, 'customers')

urlpatterns = [
    path('api/search_customer', CustomerSearchView.as_view(), name='search_customer'),
] + router.urls


from rest_framework import routers
from django.urls import path
from .api import OrganizationViewSet, GetOrganizationView


router = routers.DefaultRouter()
router.register('api/organization', OrganizationViewSet, 'organizations')

urlpatterns = [
    path('api/get_organization', GetOrganizationView.as_view(), name='get_organization'),
] + router.urls

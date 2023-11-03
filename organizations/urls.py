from rest_framework import routers
from django.urls import path
from .api import OrganizationViewSet, GetOrganizationView, CreateOrganizationAndStaffView,OrganizationListView


router = routers.DefaultRouter()
router.register('api/organization', OrganizationViewSet, 'organizations')

urlpatterns = [
    path('api/get_organization', GetOrganizationView.as_view(), name='get_organization'),
    path('api/create_organization', CreateOrganizationAndStaffView.as_view(), name='create-organization-and-staff'),
    path('api/list_organization/', OrganizationListView.as_view(), name='list-organization-and-staff'),
] + router.urls
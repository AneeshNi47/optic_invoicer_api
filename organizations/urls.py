from rest_framework import routers
from django.urls import path
from .api import OrganizationViewSet, CheckOrganizationValidity,GetOrganizationView, CreateOrganizationAndStaffView,ModelReportsOrganizationData, OrganizationListView,RefreshOrganizationData, ReportsOrganizationData


router = routers.DefaultRouter()
router.register('api/organization', OrganizationViewSet, 'organizations')

urlpatterns = [
    path('api/subscription_check', CheckOrganizationValidity.as_view(), name='organization_validity'),
    path('api/get_organization', GetOrganizationView.as_view(), name='get_organization'),
    path('api/refresh_organization', RefreshOrganizationData.as_view(), name='refresh_organization'),
    path('api/report_organization', ReportsOrganizationData.as_view(), name='report_organization'),
    path('api/model_report_organization', ModelReportsOrganizationData.as_view(), name='model_report_organization'),
    path('api/create_organization/', CreateOrganizationAndStaffView.as_view(), name='create-organization-and-staff'),
    path('api/list_organization/', OrganizationListView.as_view(), name='list-organization-and-staff'),
] + router.urls
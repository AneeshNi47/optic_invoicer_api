from rest_framework import routers
from django.urls import path
from .api import OrganizationViewSet,SubscriptionViewSet,CheckUsernameView, CheckOrganizationValidity,GetOrganizationView,CheckMailService, CreateOrganizationAndStaffView,ModelReportsOrganizationData, OrganizationListView,RefreshOrganizationData, ReportsOrganizationData


router = routers.DefaultRouter()
router.register('api/organization', OrganizationViewSet, 'organizations')

urlpatterns = [
    path('api/subscription_check', CheckOrganizationValidity.as_view(), name='organization_validity'),
    path('api/email_check', CheckMailService.as_view(), name='check_mail_service'),
    path('api/subscription', SubscriptionViewSet.as_view({
        'get': 'list',  # HTTP GET to list subscriptions
        'post': 'create',  # HTTP POST to create a subscription
    }), name='subscription'),
    path('api/subscriptions/<int:pk>/', SubscriptionViewSet.as_view({
        'get': 'retrieve',  # HTTP GET to retrieve a specific subscription
        'put': 'update',  # HTTP PUT to update a specific subscription
        'patch': 'partial_update',  # HTTP PATCH for partial updates
        'delete': 'destroy',  # HTTP DELETE to delete a subscription
    }), name='subscription-detail'),
    path('api/get_organization', GetOrganizationView.as_view(), name='get_organization'),
    path('api/refresh_organization', RefreshOrganizationData.as_view(), name='refresh_organization'),
    path('api/report_organization', ReportsOrganizationData.as_view(), name='report_organization'),
    path('api/check_username', CheckUsernameView.as_view(), name='check_username'),
    path('api/model_report_organization', ModelReportsOrganizationData.as_view(), name='model_report_organization'),
    path('api/create_organization/', CreateOrganizationAndStaffView.as_view(), name='create-organization-and-staff'),
    path('api/list_organization/', OrganizationListView.as_view(), name='list-organization-and-staff'),
] + router.urls
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import StaffViewSet, send_invitation, register_staff

# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'', StaffViewSet)

urlpatterns = [
    path('api/staff', include(router.urls)),  # This will include the CRUD routes for staff
    path('send_invitation/', send_invitation, name='send_invitation'),
    path('register_staff/<str:token>/', register_staff, name='register_staff'),
]

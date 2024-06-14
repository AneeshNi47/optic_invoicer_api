
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Optic Invoicer By Brocode Solutions",
        default_version='v1',),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include('accounts.urls')),
    path("", include('customers.urls')),
    path("", include('organizations.urls')),
    path("", include('inventory.urls')),
    path("", include('invoices.urls')),
    path("",  include('staff.urls')),
    path("",  include('wholesale.urls')),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0),name='schema-swagger-ui'),

]

# optic_invoicer_api/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import invoices.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "optic_invoicer_api.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            invoices.routing.websocket_urlpatterns
        )
    ),
})

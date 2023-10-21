from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from invoices import consumers  

websocket_urlpatterns = [
    path("ws/invoices/", consumers.InvoicesConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "websocket": URLRouter(websocket_urlpatterns),
})

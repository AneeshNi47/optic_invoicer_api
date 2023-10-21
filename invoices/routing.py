# invoices/routing.py
from django.urls import path
from . import consumers  

websocket_urlpatterns = [
    path('ws/invoice/', consumers.InvoicesConsumer.as_asgi()),
]

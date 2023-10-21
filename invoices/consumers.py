import json
from channels.generic.websocket import AsyncWebsocketConsumer

class InvoicesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("invoices", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("invoices", self.channel_name)

    async def new_lead(self, event):
        await self.send(text_data=json.dumps(event))

    async def deleted_lead(self, event):
        await self.send(text_data=json.dumps(event))

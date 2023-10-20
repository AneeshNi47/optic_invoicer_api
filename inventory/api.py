from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Inventory
from .serializers import InventorySerializer

class InventoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InventorySerializer

    def get_queryset(self):
        user = self.request.user
        return Inventory.objects.filter(organization=self.request.get_organization(), is_active=True)

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(organization=self.request.get_organization(), created_by=user)

    def perform_update(self, serializer):
        user = self.request.user
        serializer.save(updated_by=user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

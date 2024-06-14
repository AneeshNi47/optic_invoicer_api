from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import WholeSaleVendor, WholeSaleInventory, WholeSaleOrder, WholeSaleClient
from .serializer.WholeSaleVendorSerializer import WholeSaleVendorSerializer
from .serializer.WholeSaleInventorySerializer import WholeSaleInventorySerializer
from .serializer.WholeSaleOrderSerializer import WholeSaleOrderSerializer, WholeSaleOrderListSerializer
from .serializer.WholeSaleClientSerializer import WholeSaleClientSerializer

class WholeSaleVendorViewSet(viewsets.ModelViewSet):
    serializer_class = WholeSaleVendorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WholeSaleVendor.objects.filter(organization=self.request.get_organization())

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

class WholeSaleInventoryViewSet(viewsets.ModelViewSet):
    serializer_class = WholeSaleInventorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        organization = self.request.get_organization()
        return WholeSaleInventory.objects.filter(organization=organization)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class WholeSaleClientViewSet(viewsets.ModelViewSet):
    serializer_class = WholeSaleClientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        organization = self.request.get_organization()
        return WholeSaleClient.objects.filter(organization=organization)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class WholeSaleOrderViewSet(viewsets.ModelViewSet):
    serializer_class = WholeSaleOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        request = self.request
        return WholeSaleOrder.objects.filter(organization=request.get_organization())

    def get_serializer_class(self):
        if self.action == 'list':
            return WholeSaleOrderListSerializer
        return WholeSaleOrderSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
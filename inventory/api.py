from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Inventory
from .serializers import InventorySerializer, BulkInventorySerializer

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


class BulkInventoryCreateView(APIView):
    serializer_class = BulkInventorySerializer

    def post(self, request, *args, **kwargs):
        organization = request.get_organization() 
        if not organization:
            return Response({'error': 'User is not associated with any organization.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventorySearchView(APIView):
    """
    Search inventory based on SKU or name.
    """

    def get(self, request):
        sku = request.query_params.get('sku', None)
        name = request.query_params.get('name', None)
        type = request.query_params.get('type', None)

        if not (sku or name or type):
            return Response({"error": "Provide name, sku or type for searching."}, status=status.HTTP_400_BAD_REQUEST)

        if sku:
            items = Inventory.objects.filter(store_sku__icontains=sku)
        elif name:
            items = Inventory.objects.filter(name__icontains=name)
        elif type:
            items = Inventory.objects.filter(item_type__icontains=type)

        serializer = InventorySerializer(items, many=True)
        return Response(serializer.data)
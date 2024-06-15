from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from optic_invoicer_api.custom_cursor_pagination import CustomCursorPagination
from organizations.utils import check_create_invoice_permission
from .models import Inventory, InventoryCSV
from .tasks import download_and_process_file
from .serializers import InventorySerializer, BulkInventorySerializer, InventoryCSVSerializer


class InventoryViewSet(viewsets.ModelViewSet):
    """
    post:
    Create a new Inventory with Super Staff.

    # Request Sample
    ```

    {
        "store_sku": "store_sku_0L002",
        "name": "Oakley lens 1",
        "description": "this is a test lens from Oakley",
        "qty": 15,
        "sale_value": 120.45,
        "cost_value": 80.25,
        "brand": "Oakley",
        "item_type": "Lens"
    }
    ```

    # Response Sample
    ```
    {
        "id": 76,
        "item_type": "Frames",
        "SKU": "ORGA0002020231208062102519160529",
        "store_sku": "store_sku_0F01245",
        "name": "Oakley Frame 23",
        "description": "this is a test Frame from Oakley",
        "qty": 100,
        "sale_value": "354.45",
        "cost_value": "154.25",
        "brand": "Oakley",
        "is_active": true,
        "status": "Stocked",
        "created_on": "2023-12-08T06:21:02.520401Z",
        "updated_on": "2023-12-08T06:21:02.520435Z",
        "created_by": 2,
        "updated_by": null,
        "organization": 1
    }
    ```
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InventorySerializer

    def get_queryset(self):
        organization = self.request.get_organization()
        return Inventory.objects.filter(organization=organization, is_active=True)

    def perform_create(self, serializer):
        user = self.request.user
        organization = self.request.get_organization()
        latest_subscription, create_invoice_permission = check_create_invoice_permission(organization)
        if not create_invoice_permission:
            raise PermissionDenied({"error": f"Your {latest_subscription.subscription_type} subscription has ended. Please contact the administrator to add more Inventory."})
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
    permission_classes = [permissions.IsAuthenticated]
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
    permission_classes = [permissions.IsAuthenticated]

    """
    Search inventory based on SKU or name.
    """

    def get(self, request):
        organization = request.get_organization()
        sku = request.query_params.get('sku', None)
        name = request.query_params.get('name', None)
        type = request.query_params.get('type', None)

        if not (sku or name or type):
            return Response({"error": "Provide name, sku or type for searching."}, status=status.HTTP_400_BAD_REQUEST)
        queryset = Inventory.objects.filter(organization=organization)
        if sku:
            queryset = queryset.filter(store_sku__icontains=sku)
        elif name:
            queryset = queryset.filter(name__icontains=name)
        elif type:
            queryset = queryset.filter(item_type__icontains=type)

        # Apply custom cursor pagination
        paginator = CustomCursorPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = InventorySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = InventorySerializer(queryset, many=True)
        return Response(serializer.data)


class InventoryCSVViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InventoryCSVSerializer

    def get_queryset(self):
        user = self.request.user
        return InventoryCSV.objects.filter(organization=self.request.get_organization())

    def perform_create(self, serializer):
        serializer.save(organization=self.request.get_organization(), created_by=user)


class ProcessCSVViewSet(APIView):
    def get(self, request, format=None):
        organization = self.request.get_organization()
        download_and_process_file(request.GET.get('file_id'), organization)
        return Response({"message": "Method executed"})

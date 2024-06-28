from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from optic_invoicer_api.custom_cursor_pagination import CustomCursorPagination
from organizations.utils import check_create_invoice_permission
from .models import Inventory, InventoryCSV
from .tasks import download_and_process_file
from .serializers import InventorySerializer, BulkInventorySerializer, InventoryCSVSerializer
from django.db.models import Q
from django.db import connection


class InventoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InventorySerializer

    def get_queryset(self):
        organization = self.request.get_organization()
        queryset = Inventory.objects.filter(organization=organization, is_active=True)
        connection.close()
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        organization = self.request.get_organization()
        latest_subscription, create_invoice_permission = check_create_invoice_permission(organization)
        if not create_invoice_permission:
            raise PermissionDenied({
                "error": f"Your {latest_subscription.subscription_type} subscription has ended. "
                         f"Please contact the administrator to add more Inventory."
            })
        serializer.save(organization=organization, created_by=user)
        connection.close()

    def perform_update(self, serializer):
        user = self.request.user
        serializer.save(updated_by=user)
        connection.close()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        connection.close()
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
            connection.close()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        connection.close()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventorySearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        organization = request.get_organization()
        sku = request.query_params.get('sku')
        name = request.query_params.get('name')
        item_type = request.query_params.get('type')

        if not (sku or name or item_type):
            return Response({"error": "Provide name, SKU, or type for searching."}, status=status.HTTP_400_BAD_REQUEST)

        query = Q(organization=organization)
        if sku:
            query &= Q(store_sku__icontains=sku)
        if name:
            query &= Q(name__icontains=name)
        if item_type:
            query &= Q(item_type__icontains=item_type)

        queryset = Inventory.objects.filter(query)

        paginator = CustomCursorPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = InventorySerializer(page, many=True)
            connection.close()
            return paginator.get_paginated_response(serializer.data)

        serializer = InventorySerializer(queryset, many=True)
        connection.close()
        return Response(serializer.data)


class InventoryCSVViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InventoryCSVSerializer

    def get_queryset(self):
        organization = self.request.get_organization()
        queryset = InventoryCSV.objects.filter(organization=organization)
        connection.close()
        return queryset

    def perform_create(self, serializer):
        serializer.save(organization=self.request.get_organization(), created_by=self.request.user)
        connection.close()


class ProcessCSVViewSet(APIView):
    def get(self, request, format=None):
        organization = self.request.get_organization()
        download_and_process_file(request.GET.get('file_id'), organization)
        connection.close()
        return Response({"message": "Method executed"})

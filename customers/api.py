from .models import Customer, Prescription
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from optic_invoicer_api.custom_cursor_pagination import CustomCursorPagination
from .serializers import CustomerSerializer, PrescriptionSerializer, CustomerGetSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import connection


class CustomerViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return CustomerSerializer
        elif self.action == 'retrieve':
            return CustomerGetSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        organization = self.request.get_organization()
        phone = self.request.GET.get('phone')  # Retrieve the phone parameter from the URL
        queryset = Customer.objects.filter(organization=organization) if organization else Customer.objects.none()

        if phone:
            print(phone)
            queryset = queryset.filter(phone__icontains=phone)  # Add the phone filter if phone is present in the URL parameters

        return queryset

    def perform_create(self, serializer):
        organization = self.request.get_organization()
        if not organization:
            raise ValidationError("The user must belong to an organization to create a customer.")
        serializer.save(organization=organization)

    @action(detail=True, methods=['GET'])
    def prescriptions(self, request, pk=None):
        customer = self.get_object()
        prescriptions = Prescription.objects.filter(customer=customer)
        serializer = PrescriptionSerializer(prescriptions, many=True)
        connection.close()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def add_prescription(self, request, pk=None):
        customer = self.get_object()
        serializer = PrescriptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(customer=customer)
            connection.close()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        connection.close()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        organization = request.get_organization()
        phone = request.query_params.get('phone', None)
        email = request.query_params.get('email', None)

        if not organization:
            return Response({"error": "Organization not found."}, status=status.HTTP_400_BAD_REQUEST)

        if not (phone or email):
            return Response({"error": "Provide email or phone for searching."}, status=status.HTTP_400_BAD_REQUEST)

        query = Q(organization=organization)
        if phone:
            query &= Q(phone__icontains=phone)
        if email:
            query &= Q(email__icontains=email)

        queryset = Customer.objects.filter(query)

        paginator = CustomCursorPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = CustomerGetSerializer(page, many=True)
            connection.close()
            return paginator.get_paginated_response(serializer.data)

        serializer = CustomerGetSerializer(queryset, many=True)
        connection.close()
        return Response(serializer.data)


class PrescriptionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrescriptionSerializer

    def get_queryset(self):
        organization = self.request.get_organization()
        if organization:
            return Prescription.objects.filter(organization=organization)
        return Prescription.objects.none()

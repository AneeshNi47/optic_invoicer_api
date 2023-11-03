from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from .models import Invoice
from .serializers import InvoiceCreateSerializer, InvoiceGetSerializer
from rest_framework.response import Response
from customers.serializers import CustomerSerializer, PrescriptionSerializer
from customers.models import Customer, Prescription
from django.http import HttpResponse
from io import BytesIO
from .models import Invoice
from .create_invoice import create_invoice_pdf

class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceGetSerializer
    permission_classes = [permissions.IsAuthenticated]

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('organization',)

    def get_queryset(self):
        """
        This view should return a list of all the invoices
        for the currently authenticated user's organization.
        """
        user = self.request.user
        organization = self.request.get_organization()
        # Ensure the user has an associated staff profile and organization
        if hasattr(user, "staff") and organization:
            return Invoice.objects.filter(organization=organization).select_related('customer', 'prescription')
        return Invoice.objects.none()  # Return an empty queryset if conditions aren't met


class CreateInvoiceView(APIView):
    def post(self, request):
        customer_data = request.data.get('customer')
        prescription_data = request.data.get('prescription')
        organization = request.get_organization()
        customer_data['organization'] = organization
        prescription_data['organization'] = organization
        # Handle Customer
        customer_id = customer_data.get('id')
        if customer_id:
            # Update existing customer
            print("customer already available")
            customer_instance = Customer.objects.get(id=customer_id)
            customer_data['id'] = customer_instance.id
            print("customer already available",customer_instance.phone)
            customer_serializer = CustomerSerializer(customer_instance, data=customer_data, context={'request': request})
        else:
            # Create new customer
            customer_data['organization'] = organization
            customer_serializer = CustomerSerializer(data=customer_data, context={'request': request})
        if not customer_serializer.is_valid():
            print("customer creation error")
            return Response(customer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        customer = customer_serializer.save(organization=request.get_organization())
        # Handle Prescription
        prescription_serializer = PrescriptionSerializer(data=prescription_data, context={'request': request})
        if not prescription_serializer.is_valid():
            return Response(prescription_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        prescription = prescription_serializer.save(customer=customer, organization=request.get_organization())
        # Create Invoice
        invoice_data = request.data.copy()
        invoice_data['customer'] = customer.id
        invoice_data['prescription'] = prescription.id
        invoice_serializer = InvoiceCreateSerializer(data=invoice_data, context={'request': request})
        if not invoice_serializer.is_valid():
            return Response(invoice_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        invoice = invoice_serializer.save(organization=request.get_organization(), created_by=request.user)
        return Response(invoice_serializer.data, status=status.HTTP_201_CREATED)
    
    def put(self, request, *args, **kwargs):
        invoice_id = request.data.get('id')
        customer_data = request.data.get('customer')
        prescription_data = request.data.get('prescription')
        invoice_data = request.data
        # Get existing instances
        try:
            invoice_instance = Invoice.objects.get(id=invoice_id)
            customer_instance = Customer.objects.get(id=customer_data['id'])
            prescription_instance = Prescription.objects.get(id=prescription_data['id'])
        except (Invoice.DoesNotExist, Customer.DoesNotExist, Prescription.DoesNotExist):
            return Response({'error': 'Instances not found'}, status=status.HTTP_404_NOT_FOUND)
        # Update Customer
        customer_serializer = CustomerSerializer(customer_instance, data=customer_data, context={'request': request}, partial=True)
        if not customer_serializer.is_valid():
            return Response(customer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        customer = customer_serializer.save()
        # Update Prescription
        prescription_serializer = PrescriptionSerializer(prescription_instance, data=prescription_data, context={'request': request}, partial=True)
        if not prescription_serializer.is_valid():
            return Response(prescription_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        prescription = prescription_serializer.save()
        # Update Invoice
        invoice_data['customer'] = customer.id
        invoice_data['prescription'] = prescription.id
        invoice_serializer = InvoiceCreateSerializer(invoice_instance, data=invoice_data, context={'request': request}, partial=True)
        if not invoice_serializer.is_valid():
            return Response(invoice_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        invoice = invoice_serializer.save()
        return Response(invoice_serializer.data, status=status.HTTP_200_OK)

class InvoicePDFView(APIView):
    serializer_class = InvoiceGetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id)

        tear_away = request.GET.get('tear_away', True)
        only_tear_away = request.GET.get('only_tear_away', True)
        # Check if the user's organization matches the invoice's organization
        print(request.get_organization().id)
        if invoice.organization != request.get_organization():
            raise PermissionDenied
        setattr(invoice, "organization", request.get_organization())
        response = create_invoice_pdf("etst", invoice, tear_away,only_tear_away)

        return response

from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from .models import Invoice, InvoicePayment
from .serializers import InvoiceCreateSerializer, InvoiceGetSerializer, InvoicePaymentSerializer
from rest_framework.response import Response
from customers.serializers import CustomerSerializer, PrescriptionSerializer
from customers.models import Customer, Prescription
from django.http import HttpResponse
from io import BytesIO
from .models import Invoice
from .create_invoice import create_invoice_pdf, create_invoice_pdf_customer

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
            return Invoice.objects.filter(organization=organization, is_active=True).select_related('customer', 'prescription')
        return Invoice.objects.none()  # Return an empty queryset if conditions aren't met


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CreateInvoiceView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
            # Retrieve invoice ID from query parameters
        invoice_id = request.query_params.get('id')

        if not invoice_id:
            return Response({"error": "Invoice ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the invoice instance
            invoice = Invoice.objects.get(id=invoice_id)
            invoice.save()
            return Response(status=status.HTTP_202_ACCEPTED)
        except Invoice.DoesNotExist:
            raise Response( {"error": "Invoice does not exist."},status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request):
        # Prepare data for serialization
        data = request.data
        data['organization'] = request.get_organization()
        # Serialize and validate data
        serializer = InvoiceCreateSerializer(data=data, context={'request': request})
        # Check validation status
        if serializer.is_valid():
            # Data is valid, create Invoice
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Data is invalid, return error
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
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
        # Check if the user's organization matches the invoice's organization
        if invoice.organization != request.get_organization():
            raise PermissionDenied
        setattr(invoice, "organization", request.get_organization())
        response = create_invoice_pdf("organization_copy", invoice)

        return response



class InvoiceCustomerPDFView(APIView):
    serializer_class = InvoiceGetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        # Check if the user's organization matches the invoice's organization
        if invoice.organization != request.get_organization():
            raise PermissionDenied
        setattr(invoice, "organization", request.get_organization())
        response = create_invoice_pdf_customer("customer_copy", invoice)

        return response
class InvoicePaymentViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing invoice payment instances.
    """
    serializer_class = InvoicePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the invoice payments
        for the currently authenticated user's organization.
        """
        user_organization = self.request.get_organization()
        queryset = InvoicePayment.objects.filter(organization=user_organization, is_active=True)

        invoice_id = self.request.query_params.get('invoice_id')
        if invoice_id:
            queryset = queryset.filter(invoice__id=invoice_id)

        return queryset

    def perform_create(self, serializer):
        # Set the organization and created_by when creating a new InvoicePayment
        serializer.save(
            organization=self.request.get_organization(), 
            created_by=self.request.user
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user_organization = request.get_organization()
        if instance.organization != user_organization:
            return Response({"error": "You do not have permission to delete this payment"}, status=status.HTTP_403_FORBIDDEN)

        # Check if the invoice status is Delivered or Scrapped
        if instance.invoice.status in ["Delivered", "Scrapped"]:
            return Response({"error": "Cannot delete payment for delivered or scrapped invoices"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Soft delete logic
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
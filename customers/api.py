from .models import Customer, Prescription
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from optic_invoicer_api.custom_cursor_pagination import CustomCursorPagination
from .serializers import CustomerSerializer, PrescriptionSerializer,CustomerGetSerializer
from rest_framework.decorators import action
from rest_framework.response import Response

class CustomerViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    def get_serializer_class(self):
        if self.action == 'list':
            return CustomerSerializer
        elif self.action == 'retrieve':
            return CustomerGetSerializer
        return super().get_serializer_class() 

    def get_queryset(self):
        # Use the organization set in the middleware to filter customers
        if self.request.get_organization():
            return Customer.objects.filter(organization=self.request.get_organization())
        else:
            # Handle cases where there's no associated organization
            return Customer.objects.none()

    def perform_create(self, serializer):
        # Associate the customer with the organization before saving
        if not self.request.get_organization():
            raise ValidationError("The user must belong to an organization to create a customer.")
        serializer.save(organization=self.request.get_organization())

    @action(detail=True, methods=['GET'])
    def prescriptions(self, request, pk=None):
        customer = self.get_object()
        prescriptions = Prescription.objects.filter(customer=customer)
        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def add_prescription(self, request, pk=None):
        customer = self.get_object()
        serializer = PrescriptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(customer=customer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomerSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    """
    Search customers based on email or phone.
    """

    def get(self, request):
        organization = request.get_organization()
        phone = request.query_params.get('phone', None)
        email = request.query_params.get('email', None)

        if not (phone or email):
            return Response({"error": "Provide email or phone for searching."}, status=status.HTTP_400_BAD_REQUEST)
        queryset = Customer.objects.filter(organization=organization)
        if phone:
            queryset = queryset.filter(phone__icontains=phone)
        elif email:
            queryset = queryset.filter(email__icontains=email)

        
        # Apply custom cursor pagination
        paginator = CustomCursorPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = CustomerGetSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = CustomerGetSerializer(queryset, many=True)
        return Response(serializer.data)
    
class PrescriptionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrescriptionSerializer

    def get_queryset(self):
        # Use the organization set in the middleware to filter customers
        if self.request.get_organization():
            return Prescription.objects.filter(organization=self.request.get_organization())
        else:
            # Handle cases where there's no associated organization
            return Prescription.objects.none()

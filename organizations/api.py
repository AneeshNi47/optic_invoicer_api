from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Organization
from inventory.models import Inventory
from invoices.models import Invoice
from customers.models import Customer, Prescription
from rest_framework.views import APIView
from .serializers import OrganizationSerializer, OrganizationStaffSerializer,ListOrganizationStaffSerializer

class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
    ]
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_superuser:
            return Organization.objects.filter(id=self.request.get_organization().id).first()
        else:
            # Handle unauthenticated users
            return Organization.objects.none()

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            raise serializer.ValidationError("Only superusers can create an organization.")
        serializer.save(owner=self.request.user)

class GetOrganizationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    """
    Get the User Current Organization.
    """

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        organization = Organization.objects.filter(id=request.get_organization().id).first()
        if organization:
            serializer = OrganizationSerializer(organization)
            return Response(serializer.data)
        else:
             return Response({'detail': 'Organization not found for the user.'}, status=status.HTTP_404_NOT_FOUND)

class CreateOrganizationAndStaffView(APIView):
    """
    post:
    Create a new Organization with Super Staff.

    # Request Sample
    ```
    {
        "organization": {
            "name": "Bright Vision Optics",
            "address_first_line": "789 Maple Avenue",
            "email": "sarah.jones@email.com",
            "secondary_email": "info@brightvisionoptics.com",
            "primary_phone_mobile": "555-321-9876",
            "other_contact_numbers": "555-765-4321,555-678-5432",
            "phone_landline": "555-654-3210",
            "logo": null,
            "translation_required": false,
            "country": "United States",
            "city": "Seattle",
            "post_box_number": "98101",
            "services": "Vision Correction, Eyewear Consultation, Lens Fitting",
            "is_active": true
        },
        "staff": {
            "first_name": "Sarah",
            "last_name": "Jones",
            "designation": "Managing Director",
            "phone": "555-654-0987",
            "email": "sarah.jones@email.com",
            "staff_superuser": true,
            "user": {
                "username": "sarah.jones",
                "password": "seattle2023"
            }
        }
    }
    ```

    # Response Sample
    ```
    {
        "name": "Bright Vision Optics",
        "is_active": true,
        "email": "sarah.jones@email.com",
        "primary_phone_mobile": "555-321-9876",
        "staff_count": 1,
        "superstaff_first_name": "Sarah",
        "subscription_status": {
            "status": "Demo",
            "latest_payment": null
            }
    }
    ```
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request):
        serializer = OrganizationStaffSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            organization = serializer.save(owner=request.user)
            return Response(organization, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrganizationListView(APIView):
    """
    get:
    Get List of all Organization by Super Admin
    # Response Sample
    ```
    [
    {
        "name": "Optic Invoicer",
        "is_active": true,
        "email": "info@opticinvoicer.com",
        "primary_phone_mobile": "123-456-7890",
        "staff_count": 1,
        "superstaff_first_name": null,
        "subscription_status": null
    },
    {
        "name": "Optic Invoicer 2",
        "is_active": true,
        "email": "info@opticinvoicer2.com",
        "primary_phone_mobile": "123-999-7890",
        "staff_count": 1,
        "superstaff_first_name": null,
        "subscription_status": {
            "status": "Trial",
            "latest_payment": null
        }
    },..
    ]
    ```
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if not self.request.user.is_superuser:
            raise serializer.ValidationError("Only superusers can view an organization.")

        organizations = Organization.objects.all()
        serializer = ListOrganizationStaffSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class RefreshOrganizationData(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Ensure the user belongs to an organization

        organization = Organization.objects.filter(id=request.get_organization().id).first()

        if not organization:
            return Response({'detail': 'User is not associated with any organization.'}, status=status.HTTP_400_BAD_REQUEST)

        organization = request.get_organization()

        # Calculate total inventory count
        total_inventory = Inventory.objects.filter(organization=organization.id).count()
        total_invoices = Invoice.objects.filter(organization=organization.id).count()
        total_customers = Customer.objects.filter(organization=organization.id).count()
        total_prescriptions = Prescription.objects.filter(organization=organization.id).count()

        # Update total_inventory in the organization
        organization.total_inventory = total_inventory
        organization.total_invoices = total_invoices
        organization.total_customers = total_customers
        organization.total_prescriptions = total_prescriptions
        organization.save()

        # Serialize and return the updated organization
        serializer = OrganizationSerializer(organization)
        return Response(serializer.data)
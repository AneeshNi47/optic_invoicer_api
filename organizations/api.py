from rest_framework import viewsets, permissions, status
import datetime
from rest_framework.response import Response
from customers.models import Customer
from .models import Organization, Subscription, Payment
from rest_framework.views import APIView
from .serializers import OrganizationSerializer, OrganizationStaffSerializer,ListOrganizationStaffSerializer,ModelReportDataSerializer, ReportDataSerializer
from .utils import compute_reports, compute_statistics,get_model_object, convert_date_request_to_start_end_dates, date_request_dict
from django.db.models.functions import ExtractYear, ExtractMonth
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
        
        organization = request.get_organization()

        if not organization:
            return Response({'detail': 'User is not associated with any organization.'}, status=status.HTTP_400_BAD_REQUEST)

        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=5 * 30) 
        report_data = compute_reports(organization, start_date, end_date)
        

        # Update the statistics fields
        organization.invoice_statistics = report_data.get("invoice_statistics")
        organization.inventory_statistics =report_data.get("inventory_statistics")
        organization.prescription_statistics = report_data.get("prescription_statistics")
        organization.customer_statistics =report_data.get("customer_statistics")

        # Update total_inventory in the organization
        organization.total_inventory = report_data.get("total_inventory")
        organization.total_invoices = report_data.get("total_invoices")
        organization.total_customers = report_data.get("total_customers")
        organization.total_prescriptions = report_data.get("total_prescriptions")
        organization.save()

        # Serialize and return the updated organization
        serializer = OrganizationSerializer(organization)
        return Response(serializer.data)
    

class ModelReportsOrganizationData(APIView):
    permission_classes = [permissions.IsAuthenticated]

    
    def get(self, request):
        organization = request.get_organization()
        model = request.query_params.get('model')

        if not organization:
            return Response({'detail': 'User is not associated with any organization.'}, status=status.HTTP_400_BAD_REQUEST)

        if not model or not get_model_object(model):
            return Response({'detail': 'Model not found.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            model_object =get_model_object(model)
            date_request_string = request.query_params.get('date_request_string')
            
            if date_request_string is "all_time":
                report_end_date = None
                report_start_date = None
                get_all = True
            elif date_request_string is "custom_dates":
                start_date = request.query_params.get('start_date') 
                end_date = request.query_params.get('end_date') 
                report_end_date = end_date if end_date else datetime.date.today()
                report_start_date = start_date if start_date else datetime.date.today() - datetime.timedelta(days=5 * 30) 
                get_all = False
            elif date_request_string in date_request_dict:
                report_start_date, report_end_date = convert_date_request_to_start_end_dates(date_request_string)
                get_all = False
            else:
                report_start_date = datetime.date.today() - datetime.timedelta(days=5 * 30) 
                report_end_date = datetime.date.today()
                get_all = False
        
            
            report_queryset = compute_statistics(model_object, organization, report_start_date, report_end_date, False)
            if not get_all:
                total_count = model_object.objects.filter(organization=organization.id,created_on__range=(report_start_date.strftime('%Y-%m-%d'), report_end_date.strftime('%Y-%m-%d'))).count()
            else:
                total_count = model_object.objects.filter(organization=organization.id).count()

            # Convert stats to required format
            if model == "Invoice" or model=="Inventory":
                report_list = [{'year': stat['year'], 'month': stat['month'], 'count': stat['count'], 'value': float(stat['value'])} for stat in report_queryset]
            else:
                report_list = [{'year': stat['year'], 'month': stat['month'], 'value': stat['count']} for stat in report_queryset]
            
            report_data = {"monthly_statistics":report_list }
            report_data["model_name"]=model
            report_data['start_date'] = report_start_date
            report_data['end_date'] = report_end_date
            report_data['total_count']=total_count
            serializer = ModelReportDataSerializer(data=report_data)

            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': e}, status=status.HTTP_400_BAD_REQUEST)




class ReportsOrganizationData(APIView):
    permission_classes = [permissions.IsAuthenticated]

    
    def get(self, request):
        organization = request.get_organization()

        if not organization:
            return Response({'detail': 'User is not associated with any organization.'}, status=status.HTTP_400_BAD_REQUEST)

        date_request_string = request.query_params.get('date_request_string')

        if date_request_string is  "all_time":
            report_end_date = None
            report_start_date = None
            get_all = True
        elif date_request_string is "custom_dates":
            start_date = request.query_params.get('start_date') 
            end_date = request.query_params.get('end_date') 
            report_end_date = end_date if end_date else datetime.date.today()
            report_start_date = start_date if start_date else datetime.date.today() - datetime.timedelta(days=5 * 30) 
            get_all = False
        elif date_request_string in date_request_dict:
            report_start_date, report_end_date = convert_date_request_to_start_end_dates(date_request_string)
            get_all = False
        else:
            report_start_date = datetime.date.today() - datetime.timedelta(days=5 * 30) 
            report_end_date = datetime.date.today()
            get_all = False
            
        report_data = compute_reports(organization, report_start_date, report_end_date, get_all)
        report_data['start_date'] = report_start_date
        report_data['end_date'] = report_end_date
        serializer = ReportDataSerializer(data=report_data)

        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class CheckOrganizationValidity(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        organization =request.get_organization()
        try:
            # Fetch subscriptions for the given organization
            subscriptions = Subscription.objects.filter(organization_id=organization.id)
            
            # Prepare data for each subscription
            subscriptions_data = []
            for subscription in subscriptions:
                subscription_data = {
                    'subscription_id': subscription.id,
                    'subscription_type': subscription.subscription_type,
                    'status': subscription.status,
                    'payments': [{
                        'payment_id': payment.id,
                        'amount': payment.amount,
                        'payment_mode': payment.payment_mode,
                        'created_on': payment.created_on
                    } for payment in subscription.payments.all()]
                }
                subscriptions_data.append(subscription_data)

            return Response(subscriptions_data, status=status.HTTP_200_OK)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

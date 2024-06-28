from rest_framework import viewsets, permissions, status
import datetime
from django.contrib.auth.models import User
from rest_framework.response import Response
from django.conf import settings
from .models import Organization, Subscription
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .serializers import (
    OrganizationSerializer,
    SubscriptionSerializer,
    OrganizationStaffSerializer,
    ListOrganizationStaffSerializer,
    ModelReportDataSerializer,
    ReportDataSerializer
)
from .utils import (
    compute_reports,
    compute_statistics,
    get_model_object,
    check_create_invoice_permission,
    convert_date_request_to_start_end_dates,
    date_request_dict
)


class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_superuser:
            return Organization.objects.filter(id=self.request.get_organization().id)
        return Organization.objects.none()

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            raise serializers.ValidationError("Only superusers can create an organization.")
        serializer.save(owner=self.request.user)


class GetOrganizationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        organization = Organization.objects.filter(id=request.get_organization().id).first()
        if organization:
            serializer = OrganizationSerializer(organization)
            return Response(serializer.data)
        return Response({'detail': 'Organization not found for the user.'}, status=status.HTTP_404_NOT_FOUND)


class CreateOrganizationAndStaffView(APIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request):
        serializer = OrganizationStaffSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            organization = serializer.save(owner=request.user)
            return Response(organization, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not self.request.user.is_superuser:
            return Response({'detail': 'Only superusers can view organizations.'}, status=status.HTTP_403_FORBIDDEN)

        organizations = Organization.objects.all()
        serializer = ListOrganizationStaffSerializer(organizations, many=True)
        return Response(serializer.data)


class RefreshOrganizationData(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        organization = request.get_organization()
        if not organization:
            return Response({'detail': 'User is not associated with any organization.'}, status=status.HTTP_400_BAD_REQUEST)

        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=5 * 30)
        report_data = compute_reports(organization, start_date, end_date)

        # Update organization statistics
        organization.invoice_statistics = report_data.get("invoice_statistics")
        organization.inventory_statistics = report_data.get("inventory_statistics")
        organization.prescription_statistics = report_data.get("prescription_statistics")
        organization.customer_statistics = report_data.get("customer_statistics")
        organization.total_inventory = report_data.get("total_inventory")
        organization.total_invoices = report_data.get("total_invoices")
        organization.total_customers = report_data.get("total_customers")
        organization.total_prescriptions = report_data.get("total_prescriptions")
        organization.save()

        serializer = OrganizationSerializer(organization)
        return Response(serializer.data)


class ModelReportsOrganizationData(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        organization = request.get_organization()
        model = request.query_params.get('model')

        if not organization:
            return Response({'detail': 'User is not associated with any organization.'}, status=status.HTTP_400_BAD_REQUEST)

        model_object = get_model_object(model)
        if not model_object:
            return Response({'detail': 'Model not found.'}, status=status.HTTP_400_BAD_REQUEST)

        date_request_string = request.query_params.get('date_request_string')
        if date_request_string == "all_time":
            report_start_date, report_end_date, get_all = None, None, True
        elif date_request_string == "custom_dates":
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            report_start_date = start_date or datetime.date.today() - datetime.timedelta(days=5 * 30)
            report_end_date = end_date or datetime.date.today()
            get_all = False
        elif date_request_string in date_request_dict:
            report_start_date, report_end_date = convert_date_request_to_start_end_dates(date_request_string)
            get_all = False
        else:
            report_start_date = datetime.date.today() - datetime.timedelta(days=5 * 30)
            report_end_date = datetime.date.today()
            get_all = False

        report_queryset = compute_statistics(model_object, organization, report_start_date, report_end_date, False)
        total_count = model_object.objects.filter(
            organization=organization.id
        )
        if not get_all and report_start_date and report_end_date:
            total_count = total_count.filter(created_on__range=(report_start_date, report_end_date))

        total_count = total_count.count()

        report_list = [
            {'year': stat['year'], 'month': stat['month'], 'count': stat['count'], 'value': float(stat.get('value', 0))}
            for stat in report_queryset
        ]

        report_data = {
            "monthly_statistics": report_list,
            "model_name": model,
            "start_date": report_start_date,
            "end_date": report_end_date,
            "total_count": total_count
        }
        serializer = ModelReportDataSerializer(data=report_data)

        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReportsOrganizationData(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        organization = request.get_organization()
        if not organization:
            return Response({'detail': 'User is not associated with any organization.'}, status=status.HTTP_400_BAD_REQUEST)

        date_request_string = request.query_params.get('date_request_string')
        if date_request_string == "all_time":
            report_start_date, report_end_date, get_all = None, None, True
        elif date_request_string == "custom_dates":
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            report_start_date = start_date or datetime.date.today() - datetime.timedelta(days=5 * 30)
            report_end_date = end_date or datetime.date.today()
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
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckOrganizationValidity(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        organization = request.get_organization()
        if not organization:
            return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            latest_subscription, create_invoice_permission = check_create_invoice_permission(organization)
            if not latest_subscription:
                return Response({'message': 'No active subscriptions found'}, status=status.HTTP_200_OK)

            subscription_data = {
                'subscription_id': latest_subscription.id,
                'trial_start_date': latest_subscription.trial_start_date,
                'trial_end_date': latest_subscription.trial_end_date,
                'subscription_type': latest_subscription.subscription_type,
                'create_invoice_permission': create_invoice_permission,
                'status': latest_subscription.status,
                'created_on': latest_subscription.created_on,
                'payments': [
                    {
                        'payment_id': payment.id,
                        'amount': payment.amount,
                        'payment_mode': payment.payment_mode,
                        'created_on': payment.created_on
                    } for payment in latest_subscription.payments.all()
                ]
            }

            return Response(subscription_data)
        except Exception as error:
            return Response({'error': str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckMailService(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        organization = request.get_organization()
        test_information = {
            "test_value1": "Tester",
            "email": "dr2633@gmail.com"
        }
        try:
            mail_subject = 'Welcome to Our Platform'
            html_message = render_to_string('email/mail_check.html', {
                'test_information': test_information,
                'organization': organization,
            })
            plain_message = strip_tags(html_message)

            mail_send_status = send_mail(
                subject=mail_subject,
                message=plain_message,
                from_email=settings.EMAIL_FROM_EMAIL,
                recipient_list=[test_information['email']],
                html_message=html_message
            )
            return Response({'mail_send_status': mail_send_status})
        except Exception as error:
            return Response({'error': "Unable to send mail"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        organization = self.request.get_organization()
        if self.request.user.is_authenticated and organization:
            return Subscription.objects.filter(organization=organization.id)
        return Subscription.objects.none()


class CheckUsernameView(APIView):
    def get(self, request):
        username = request.GET.get('username')
        if not username:
            return Response({'error': 'Username parameter is missing.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'exists': True}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'exists': False})

from rest_framework import serializers
from django.db import transaction
from .models import Organization, Payment, Subscription
from staff.models import Staff
from django.contrib.auth.models import User

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'
        extra_kwargs = {
            'owner': {'required': False},  # Set 'required' to False
        }

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']

class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    organization = serializers.PrimaryKeyRelatedField(read_only=True)  # Set 'read_only' to True


    class Meta:
        model = Staff
        fields = '__all__'

    def create(self, validated_data, organization=None):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        staff = Staff.objects.create(user=user, organization=organization, **validated_data)
        return staff

class OrganizationStaffSerializer(serializers.Serializer):
    organization = OrganizationSerializer()
    staff = StaffSerializer()

    def create(self, validated_data):
        organization_data = validated_data.pop('organization')
        staff_data = validated_data.pop('staff')
        with transaction.atomic():
            organization = Organization.objects.create(**organization_data,owner=self.context['request'].user)
            staff = StaffSerializer().create(staff_data, organization=organization)
            staff.organization = organization
            staff.save()
            # Create a subscription instance with default values
            Subscription.objects.create(
                organization=organization,
                subscription_type='Demo',
                status='Trial'
            )
        saved_organization =  {
                "name": organization.name,
                "is_active": organization.is_active,
                "email": organization.email,
                "primary_phone_mobile": organization.primary_phone_mobile,
                "staff_count": 1,
                "superstaff_first_name": staff_data['first_name'],
                "subscription_status": {
                    "status": "Demo",
                    "latest_payment": None
                
                }
            }
        return saved_organization
    

class ListOrganizationStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['first_name']

class ListOrganizationPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['amount', 'created_on']  # Assuming you want to show the amount and date of the latest payment

class ListOrganizationSubscriptionSerializer(serializers.ModelSerializer):
    latest_payment = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ['status', 'latest_payment']

    def get_latest_payment(self, obj):
        latest_payment = obj.payments.order_by('-created_on').first()
        return ListOrganizationPaymentSerializer(latest_payment).data if latest_payment else None

class ListOrganizationStaffSerializer(serializers.ModelSerializer):
    superstaff_first_name = serializers.SerializerMethodField()
    staff_count = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ['name','is_active','email','primary_phone_mobile' ,'staff_count', 'superstaff_first_name', 'subscription_status']

    def get_superstaff_first_name(self, obj):
        superstaff = Staff.objects.filter(organization=obj, staff_superuser=True).first()
        return superstaff.first_name if superstaff else None

    def get_staff_count(self, obj):
        return Staff.objects.filter(organization=obj).count()

    def get_subscription_status(self, obj):
        subscription = Subscription.objects.filter(organization=obj).first()
        return ListOrganizationSubscriptionSerializer(subscription).data if subscription else None

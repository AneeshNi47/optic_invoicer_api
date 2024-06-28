from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import authenticate
from staff.models import Staff
from organizations.serializers import OrganizationSerializer
from customers.models import Customer


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)

        # Check if the user is authenticated and is active
        if user and user.is_active:
            # If the user is not a superuser, proceed with the organization check
            if not user.is_superuser:
                organization = None

                # Check if the user is associated with a Staff object
                if hasattr(user, 'staff'):
                    staff_instance = user.staff
                    organization = staff_instance.organization

                # Check if the user is associated with a Customer object
                elif hasattr(user, 'customer'):
                    customer_instance = user.customer
                    organization = customer_instance.organization

                # Ensure the user is associated with an organization
                if organization is None:
                    raise serializers.ValidationError("User is not associated with any organization.")

                # Check if the organization is active
                if not organization.is_active:
                    raise serializers.ValidationError("The associated organization is not active.")

            # User is associated with a Staff object
            if hasattr(user, 'staff'):
                staff_instance = user.staff
                org_serializer = OrganizationSerializer(staff_instance.organization)
                data['staff_details'] = {
                    'first_name': staff_instance.first_name,
                    'last_name': staff_instance.last_name,
                    'designation': staff_instance.designation,
                    'organization': org_serializer.data
                }
                data['user_type'] = "staff"
                data['user'] = user
                return data

            # User is associated with a Customer object
            elif hasattr(user, 'customer'):
                customer_instance = user.customer
                data['customer_details'] = {
                    'first_name': customer_instance.first_name,
                    'last_name': customer_instance.last_name,
                    'phone': customer_instance.phone,
                    'organization': customer_instance.organization.name
                }
                data['user_type'] = "customer"
                data['user'] = user
                return data

            # User is not associated with either Staff or Customer, assume Admin
            else:
                data['user_type'] = "admin"
                data['user'] = user
                return data

        raise PermissionDenied("Incorrect password.")


class StaffSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer()

    class Meta:
        model = Staff
        fields = ('first_name', 'last_name', 'designation', 'phone',
                  'organization', 'email', 'staff_superuser')


class CustomerSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer()

    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'phone',
                  'email', 'organization', 'gender')


class UserSerializer(serializers.ModelSerializer):
    staff_details = serializers.SerializerMethodField(read_only=True)
    customer_details = serializers.SerializerMethodField(
        read_only=True)  # Assuming you have a method for admin_details
    user_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            'groups',
            'is_superuser',
            'staff_details',
            'customer_details',
            'user_type'
        )

    def get_staff_details(self, obj):
        try:
            staff_instance = Staff.objects.get(user=obj)
            return StaffSerializer(staff_instance).data
        except Staff.DoesNotExist:
            return None

    def get_customer_details(self, obj):
        try:
            customer_instance = Customer.objects.get(user=obj)
            return CustomerSerializer(customer_instance).data
        except Customer.DoesNotExist:
            return None

    def get_user_type(self, obj):
        if obj.is_superuser:
            return 'admin'
        elif hasattr(obj, 'staff'):
            return 'staff'
        elif hasattr(obj, 'customer'):
            return 'customer'
        else:
            return 'unknown'


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user with this email found.")
        return value


class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."})
        return attrs

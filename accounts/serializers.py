from django.contrib.auth.models import User, Group
from rest_framework import serializers
from django.contrib.auth import authenticate
from staff.models import Staff
from customers.models import Customer


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)

        # Check if the user is authenticated and is active
        if user and user.is_active:
            # Check if the user is associated with a Staff object
            if hasattr(user, 'staff'):
                staff_instance = user.staff
                data['staff_details'] = {
                    'first_name': staff_instance.first_name,
                    'last_name': staff_instance.last_name,
                    'designation': staff_instance.designation,
                    # ... add any other fields you need ...
                }
                data['user_type'] = "staff"
                return data

            # Check if the user is associated with a Customer object
            elif hasattr(user, 'customer'):
                customer_instance = user.customer
                data['customer_details'] = {
                    'first_name': customer_instance.first_name,
                    'last_name': customer_instance.last_name,
                    'phone': customer_instance.phone,
                    # ... add any other fields you need ...
                }
                data['user_type'] = "customer"
                return data

            # If the user is not associated with either, raise an error
            else:
                data['user_type'] = "admin"
                return data

        raise serializers.ValidationError("Incorrect Credentials.")


    
class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ('first_name', 'last_name', 'designation', 'phone', 'email', 'staff_superuser')

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'phone', 'email', 'gender')

class UserSerializer(serializers.ModelSerializer):
    staff_details = serializers.SerializerMethodField(read_only=True)
    customer_details = serializers.SerializerMethodField(read_only=True)  # Assuming you have a method for admin_details
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

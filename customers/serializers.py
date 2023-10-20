from .models import Customer, Prescription
from rest_framework import serializers

class CustomerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    class Meta:
        model= Customer
        fields = '__all__'
        read_only_fields = ('organization',)

    def validate(self, data):
        organization = None

        # Check if 'request' is in context and if it has 'get_organization' method
        if 'request' in self.context and hasattr(self.context['request'], 'get_organization'):
            organization = self.context['request'].get_organization()

        if not organization:
            raise serializers.ValidationError("Organization could not be determined from the request context.")

        phone = data.get('phone')
        email = data.get('email')
        customer_id = data.get('id', None)

        # Check for phone uniqueness
        phone_query = Customer.objects.filter(organization=organization, phone=phone)
        if customer_id:
            phone_query = phone_query.exclude(id=customer_id)
        if phone_query.exists():
            raise serializers.ValidationError({"phone": "This phone number is already registered in the organization."})

        # Check for email uniqueness
        email_query = Customer.objects.filter(organization=organization, email=email)
        if customer_id:
            email_query = email_query.exclude(id=customer_id)
        if email_query.exists():
            raise serializers.ValidationError({"email": "This email is already registered in the organization."})

        return data






class PrescriptionSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), required=False)
    class Meta:
        model= Prescription
        fields = '__all__'
        read_only_fields = ('organization',)
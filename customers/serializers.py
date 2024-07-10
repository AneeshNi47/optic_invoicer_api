from .models import Customer, Prescription
from rest_framework import serializers
from invoices.models import Invoice


class InvoiceCustomerGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('organization',)


class PrescriptionGetSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), required=False)

    class Meta:
        model = Prescription
        exclude = ('organization',)
        read_only_fields = ('organization',)


class CustomerGetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    prescriptions = PrescriptionGetSerializer(many=True, read_only=True)  # Add this line
    invoices = InvoiceCustomerGetSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        exclude = ('organization',)
        read_only_fields = ('organization',)


class CustomerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Customer
        exclude = ('organization',)
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
        if email:
            email_query = Customer.objects.filter(organization=organization, email=email)
            if customer_id:
                email_query = email_query.exclude(id=customer_id)
            if email_query.exists():
                raise serializers.ValidationError({"email": "This email is already registered in the organization."})

        return data


class PrescriptionSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), required=False)

    class Meta:
        model = Prescription
        exclude = ('organization',)
        read_only_fields = ('organization',)

    def to_internal_value(self, data):
        # Convert integer-like inputs to floats for specific fields
        float_fields = ['left_sphere', 'right_sphere', 'left_cylinder', 'right_cylinder',
                        'left_prism', 'right_prism', 'left_add', 'right_add',
                        'left_ipd', 'right_ipd']

        if isinstance(data, dict):
            for field in float_fields:
                if field in data and data[field] is not None:
                    try:
                        data[field] = float(data[field])
                    except (ValueError, TypeError):
                        raise serializers.ValidationError({field: "This field must be a number."})
        else:
            raise TypeError("Expected data to be a dictionary")

        return super().to_internal_value(data)

    def validate(self, data):
        # Centralized validation for choice fields
        choice_fields = {
            'left_sphere': Prescription.SPHERE_CHOICES,
            'right_sphere': Prescription.SPHERE_CHOICES,
            'left_cylinder': Prescription.CYLINDER_CHOICES,
            'right_cylinder': Prescription.CYLINDER_CHOICES,
            'left_axis': Prescription.AXIS_CHOICES,
            'right_axis': Prescription.AXIS_CHOICES,
            'left_prism': Prescription.PRISM_CHOICES,
            'right_prism': Prescription.PRISM_CHOICES,
            'left_add': Prescription.ADD_CHOICES,
            'right_add': Prescription.ADD_CHOICES
        }
        for field, choices in choice_fields.items():
            if field in data:
                self._validate_choice_field(data[field], choices)
        return data

    def _validate_choice_field(self, value, choices):
        if value is None:
            return
        if value not in dict(choices):
            raise serializers.ValidationError(f"Invalid choice for {value}.")

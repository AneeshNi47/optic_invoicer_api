from rest_framework import serializers
from .models import Staff

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = '__all__'

    def validate(self, data):
        # Check if a staff with staff_superuser=True already exists for the organization
        if data.get('staff_superuser', False):
            existing_superuser = Staff.objects.filter(organization=data['organization'], staff_superuser=True).exists()
            if existing_superuser:
                raise serializers.ValidationError("An organization can have only one staff with superuser privileges.")
        return data

    def create(self, validated_data):
        staff = Staff.objects.create(**validated_data)
        return staff

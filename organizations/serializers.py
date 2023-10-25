from rest_framework import serializers
from .models import Organization
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

        organization = Organization.objects.create(**organization_data,owner=self.context['request'].user)
        staff = StaffSerializer().create(staff_data, organization=organization)
        staff.organization = organization
        staff.save()

        return organization
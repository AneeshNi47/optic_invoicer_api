from rest_framework import serializers 
from ..models import WholeSaleVendor, WholeSaleInventory

class WholeSaleVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = WholeSaleVendor
        fields = '__all__'
        read_only_fields = ('created_by', 'updated_by', 'created_on', 'updated_on', 'organization')

    def create(self, validated_data):
        request = self.context['request']
        organization = request.get_organization() 
        validated_data['organization'] = organization
        validated_data['created_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['updated_by'] = user
        return super().update(instance, validated_data)



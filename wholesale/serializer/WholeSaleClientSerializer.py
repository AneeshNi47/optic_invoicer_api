from rest_framework import serializers
from ..models import WholeSaleClient

class WholeSaleClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = WholeSaleClient
        fields = '__all__'
        read_only_fields = ('total_orders', 'total_credit', 'total_payment', 'last_payment_date', 'last_order_date', 'is_active', 'created_by', 'updated_by', 'created_on', 'updated_on', 'organization')

    def create(self, validated_data):
        request = self.context['request']
        organization = request.get_organization()
        
        wholesale_client = WholeSaleClient.objects.create(
            organization=organization,
            **validated_data
        )
        return wholesale_client

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['updated_by'] = user
        return super().update(instance, validated_data)

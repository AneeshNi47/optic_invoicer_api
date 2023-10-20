from rest_framework import serializers
from .models import Inventory

class InventorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Inventory
        fields = '__all__'
        read_only_fields = ('organization',)

    def validate(self, data):
        user = self.context['request'].user

        if 'organization' in data and data['organization'] != user.get_organization(): 
            raise serializers.ValidationError("You cannot create or update inventory for another organization.")

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        request = self.context['request']
        organization = request.get_organization() 
        validated_data['created_by'] = user
        validated_data['organization'] = organization
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['updated_by'] = user
        return super().update(instance, validated_data)

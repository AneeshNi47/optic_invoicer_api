from rest_framework import serializers
from .models import Inventory, InventoryCSV

class InventorySerializer(serializers.ModelSerializer):
    item_type = serializers.ChoiceField(choices=Inventory.TYPE_CHOICES)


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

class BulkInventorySerializer(serializers.Serializer):
    inventories = InventorySerializer(many=True)

    def create(self, validated_data):
        org_id = self.context['request'].get_organization()

        # Set organization_id for each item
        inventories_data = validated_data.pop('inventories')
        inventories_objects = []
        for item in inventories_data:
            inventory = Inventory(organization=org_id, **item)
            # Generate and set the SKU
            inventory.SKU = inventory.generate_sku()
            # Append the Inventory object to the list
            inventories_objects.append(inventory)
        return Inventory.objects.bulk_create(inventories_objects)

    def to_representation(self, obj):
        # obj here should be a list of Inventory instances
        # so we'll serialize it using the InventorySerializer
        serializer = InventorySerializer(obj, many=True)
        return {'inventories': serializer.data}



class InventoryCSVSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryCSV
        fields = '__all__'
        read_only_fields = ('organization',)
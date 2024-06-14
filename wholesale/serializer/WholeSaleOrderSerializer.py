from rest_framework import serializers
from django.db import transaction
from ..models import  WholeSaleOrder, SalesOrderItems,WholeSaleInventory


class WholeSaleOrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WholeSaleOrder
        fields = '__all__'
        read_only_fields = ('order_no', 'created_by', 'updated_by', 'created_on', 'updated_on', 'organization')

class WholeSaleInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WholeSaleInventory
        fields = [
            'item_code', 'item_type', 'item_property', 'group', 'category',
            'item_name', 'description', 'brand', 'origin', 'part_model_no',
            'size', 'color'
        ]

class SalesOrderItemsSerializer(serializers.ModelSerializer):
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)
    inventory_item = WholeSaleInventorySerializer(read_only=True)  # Use nested serializer for inventory_item


    class Meta:
        model = SalesOrderItems
        fields = '__all__'
        extra_kwargs = {
            'order': {'required': False}  # Make 'order' not required for validation
        }



class WholeSaleOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemsSerializer(many=True, read_only=True)
    
    class Meta:
        model = WholeSaleOrder
        fields = '__all__'
        read_only_fields = ('order_no','created_by', 'updated_by', 'created_on', 'updated_on', 'organization')

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context['request']
        user = request.user
        validated_data['organization'] = request.get_organization()
        validated_data['created_by'] = user

        # Create the WholeSaleOrder object
        with transaction.atomic():
            wholesale_order = WholeSaleOrder.objects.create(**validated_data)

            total_amount = 0
            total_discount = 0
            total_tax = 0
            total_payment = 0
            client = wholesale_order.client
            tax_percentage = client.tax_percentage / 100 

            # Create the SalesOrderItems
            for item_data in items_data:
                inventory_item = item_data['inventory_item']
                quantity = item_data['quantity']
                selected_selling_price = item_data['selected_selling_price']
                discount_percentage = item_data['discount_percentage']

                # Check if the discount_percentage exceeds the max_discount_percentage
                if discount_percentage > inventory_item.max_discount_percentage:
                    raise serializers.ValidationError(f'Discount for item {inventory_item.item_name} exceeds the maximum allowed discount.')

                # Check if the quantity exceeds the available quantity
                if quantity > inventory_item.re_order_qty:
                    raise serializers.ValidationError(f'Quantity for item {inventory_item.item_name} exceeds available stock.')

                SalesOrderItems.objects.create(
                    order=wholesale_order,
                    inventory_item=inventory_item,
                    quantity=quantity,
                    selected_selling_price=selected_selling_price,
                    discount_percentage=discount_percentage
                )

                # Calculate the total amounts
                item_total = selected_selling_price * quantity
                item_discount = item_total * discount_percentage / 100
                total_amount += item_total
                total_discount += item_discount
                total_tax += (item_total - item_discount) * tax_percentage  # Assuming 10% tax rate
                total_payment += item_total - item_discount  # Example calculation

            # Update the WholeSaleOrder with the calculated amounts
            wholesale_order.total_amount = total_amount
            wholesale_order.total_discount = total_discount
            wholesale_order.total_tax = total_tax
            wholesale_order.total_payment = total_payment
            wholesale_order.save()

            return wholesale_order

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['updated_by'] = user
        return super().update(instance, validated_data)
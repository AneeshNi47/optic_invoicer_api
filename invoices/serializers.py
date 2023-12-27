from rest_framework import serializers
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from .models import Invoice, InvoicePayment, InvoiceItem
from inventory.serializers import InventorySerializer
from inventory.models import Inventory

from customers.serializers import CustomerSerializer, PrescriptionSerializer
from customers.models import Customer, Prescription

class InvoiceItemWriteSerializer(serializers.ModelSerializer):
    inventory_item = serializers.PrimaryKeyRelatedField(queryset=Inventory.objects.all())

    class Meta:
        model = InvoiceItem
        fields = ['inventory_item', 'quantity']


class InvoiceCreateSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    prescription = PrescriptionSerializer()
    inventory_items = InvoiceItemWriteSerializer(many=True)


    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('organization',)

    @transaction.atomic
    def create(self, validated_data):
        customer_data = validated_data.pop('customer')
        prescription_data = validated_data.pop('prescription')
        inventory_items = validated_data.pop('inventory_items', [])

        # Handle Customer
        customer_id = customer_data.get('id')
        if customer_id:
            # Update existing customer
            customer_instance = Customer.objects.get(id=customer_id)
            customer_serializer = CustomerSerializer(customer_instance, data=customer_data, context={'request': self.context['request']})
        else:
            # Create new customer
            customer_serializer = CustomerSerializer(data=customer_data, context={'request': self.context['request']})
        customer_serializer.is_valid(raise_exception=True)
        customer = customer_serializer.save(organization=self.context['request'].get_organization())

        # Handle Prescription
        prescription_id = prescription_data.get('id')
        if prescription_id:
            # Update existing prescription
            prescription_instance = Prescription.objects.get(id=prescription_id)
            prescription_serializer = PrescriptionSerializer(prescription_instance, data=prescription_data)
        else:
            # Create new Prescription
            prescription_serializer = PrescriptionSerializer(data=prescription_data)
        prescription_serializer.is_valid(raise_exception=True)
        prescription = prescription_serializer.save(customer=customer, organization=self.context['request'].get_organization())

        
        invoice = Invoice.objects.create(
            customer=customer,
            prescription=prescription,
            organization=self.context['request'].get_organization(),
            created_by=self.context['request'].user,
            **validated_data
        )
        total_price = 0

        for item_data in inventory_items:
            inventory_item_id = item_data['inventory_item']
            inventory_item = Inventory.objects.get(id=inventory_item_id.id)
            required_quantity = item_data['quantity']

            if inventory_item.qty < required_quantity:
                raise serializers.ValidationError(
                    f"Item {inventory_item.name} is out of stock or insufficient quantity."
                )

            InvoiceItem.objects.create(
                invoice=invoice,
                inventory_item=inventory_item,
                quantity=required_quantity,
                sale_value=inventory_item.sale_value,  # Capture the current sale value
                cost_value=inventory_item.cost_value,   # Capture the current cost value,
            )

            # Update Inventory
            inventory_item.qty -= required_quantity
            if inventory_item.qty == 0:
                inventory_item.status = "Out of Stock"
            inventory_item.save()
            total_price += inventory_item.sale_value * required_quantity

        invoice.total = total_price - invoice.discount
        if invoice.is_taxable:
            invoice.total = invoice.total - ((invoice.tax_percentage / 100) * invoice.total)
        invoice.balance = invoice.total - invoice.advance
        if invoice.balance < 0:
            raise ValueError("Invoice Balance calculation Error")
        invoice.save()

        return invoice
    


class InvoicePaymentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = InvoicePayment
        fields = '__all__'
        read_only_fields = ('organization',)

    def create(self, validated_data):
        return InvoicePayment.objects.create(**validated_data,
            created_by=self.context['request'].user)



class InvoiceItemSerializer(serializers.ModelSerializer):
    class InventorySerializer(serializers.ModelSerializer):
        item_type = serializers.ChoiceField(choices=Inventory.TYPE_CHOICES)


        class Meta:
            model = Inventory
            fields = (
                        "item_type",
                        "store_sku",
                        "name",
                        "brand",
                        "is_active"
            )
            read_only_fields = ('organization',)
    inventory_item = InventorySerializer(read_only=True)  # Nested serialization for detailed inventory item info

    class Meta:
        model = InvoiceItem
        fields = ['inventory_item','sale_value','cost_value', 'quantity']

class InvoiceGetSerializer(serializers.ModelSerializer):
    class CustomerPartSerializer(serializers.ModelSerializer):
        class Meta:
            model= Customer
            fields = (
                    "phone",
                    "email",
                    "first_name",
                    "last_name",
                    "gender")
            read_only_fields = ('organization',)
    class InvoicePaymentPartSerializer(serializers.ModelSerializer):
         class Meta:
            model = InvoicePayment
            fields = (
                    "amount",
                    "payment_type",
                    "payment_mode",
                    "remarks",
                    "is_active")
            read_only_fields = ('organization',)

    customer = CustomerPartSerializer()
    invoice_payment = InvoicePaymentPartSerializer(many=True, read_only=True)
    inventory_items = InvoiceItemSerializer(many=True, read_only=True, source='invoiceitem_set')


    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('organization',)



class InvoiceGetItemSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    prescription = PrescriptionSerializer()
    invoice_payment = InvoicePaymentSerializer(many=True, read_only=True)
    inventory_items = InvoiceItemSerializer(many=True, read_only=True, source='invoiceitem_set')


    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('organization',)

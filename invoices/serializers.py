from rest_framework import serializers
from django.db import transaction
from .models import Invoice, InvoicePayment
from inventory.serializers import InventorySerializer

from customers.serializers import CustomerSerializer, PrescriptionSerializer
from customers.models import Customer, Prescription
from inventory.serializers import InventorySerializer


class InvoiceCreateSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    prescription = PrescriptionSerializer()

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('organization',)

    @transaction.atomic
    def create(self, validated_data):
        customer_data = validated_data.pop('customer')
        prescription_data = validated_data.pop('prescription')
        items_data = validated_data.pop('items', [])

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

        # Create Invoice
        invoice = Invoice.objects.create(
            customer=customer,
            prescription=prescription,
            organization=self.context['request'].get_organization(),
            **validated_data
        )
        
        for item in items_data:
            invoice.items.add(item)  # Assuming items is a ManyToManyField on Invoice

        # Update total, balance, and possibly invoice_number
        total_price = sum(item.sale_value for item in invoice.items.all())
        invoice.total = total_price - invoice.discount
        invoice.balance = invoice.total - invoice.advance
        invoice.save()
        return invoice
    


class InvoicePaymentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = InvoicePayment
        fields = '__all__'
        read_only_fields = ('organization',)

    def create(self, validated_data):
        return InvoicePayment.objects.create(**validated_data)

class InvoiceGetSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    prescription = PrescriptionSerializer()
    invoice_payment = InvoicePaymentSerializer(many=True, read_only=True)
    items = InventorySerializer(many=True, read_only=True) 

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('organization',)



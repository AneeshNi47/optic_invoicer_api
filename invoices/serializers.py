from rest_framework import serializers
from .models import Invoice
from customers.serializers import CustomerSerializer, PrescriptionSerializer
from customers.models import Customer, Prescription
from inventory.serializers import InventorySerializer


class InvoiceCreateSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    prescription = serializers.PrimaryKeyRelatedField(queryset=Prescription.objects.all())


    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('organization',)
    
    def create(self, validated_data):
        items_data = validated_data.pop('items',[])


        invoice = Invoice.objects.create(
            **validated_data
        )
        invoice.items.set(items_data)
        return invoice


class InvoiceGetSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    prescription = PrescriptionSerializer()
    items = InventorySerializer(many=True, read_only=True) 

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('organization',)

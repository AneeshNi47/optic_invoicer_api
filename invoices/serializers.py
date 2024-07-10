from rest_framework import serializers
from django.db import transaction
from .models import Invoice, InvoicePayment, InvoiceItem
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
    prescription = PrescriptionSerializer(required=False)
    inventory_items = InvoiceItemWriteSerializer(many=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('organization',)

    @transaction.atomic
    def create(self, validated_data):
        customer_data = validated_data.pop('customer')
        prescription_data = validated_data.pop('prescription', None)
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
        prescription = None
        if prescription_data:
            prescription_id = prescription_data.get('id')
            if not prescription_id:
                # Create new Prescription if id is not available
                prescription_serializer = PrescriptionSerializer(data=prescription_data)
                prescription_serializer.is_valid(raise_exception=True)
                prescription = prescription_serializer.save(customer=customer, organization=self.context['request'].get_organization())
            else:
                # Link existing Prescription to the invoice
                prescription = Prescription.objects.get(id=prescription_id)

        # Create the Invoice
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
            invoice.total = invoice.total + ((invoice.tax_percentage / 100) * invoice.total)
        invoice.balance = invoice.total - invoice.advance
        if invoice.balance < 0:
            raise ValueError("Invoice Balance calculation Error")
        invoice.save()

        return invoice


class InvoiceUpdateSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(required=False)
    prescription = PrescriptionSerializer(required=False, allow_null=True)
    inventory_items = InvoiceItemWriteSerializer(many=True, required=False)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('organization',)

    def validate(self, data):
        if 'prescription' not in data:
            data['prescription'] = None
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        request_data = self.context['request'].data  # NEW LINE: Extracting request data
        prescription_data = request_data.get('prescription', None)  # NEW LINE: Getting prescription data from request_data

        customer_data = validated_data.pop('customer', None)
        inventory_items = validated_data.pop('inventory_items', None)

        # Update customer
        if customer_data:
            customer_id = customer_data.get('id')
            if customer_id:
                customer_instance = Customer.objects.get(id=customer_id)
                customer_serializer = CustomerSerializer(customer_instance, data=customer_data, context={'request': self.context['request']}, partial=True)
            else:
                customer_serializer = CustomerSerializer(data=customer_data, context={'request': self.context['request']})
            customer_serializer.is_valid(raise_exception=True)
            customer = customer_serializer.save(organization=self.context['request'].get_organization())
            instance.customer = customer

        # Handle prescription
        if prescription_data is not None:
            prescription_id = prescription_data.get('id', None)  # Using prescription_data directly from request
            if prescription_id:
                try:
                    prescription_instance = Prescription.objects.get(id=prescription_id)
                    # Manually update the instance without losing the id field
                    for attr, value in prescription_data.items():  # Using prescription_data directly from request
                        setattr(prescription_instance, attr, value)
                    prescription_instance.save()
                    instance.prescription = prescription_instance  # Assigning the updated prescription instance
                except Prescription.DoesNotExist:
                    raise serializers.ValidationError({"prescription": "Prescription with this ID does not exist."})
            else:
                prescription_serializer = PrescriptionSerializer(data=prescription_data, context={'request': self.context['request']})
                prescription_serializer.is_valid(raise_exception=True)
                prescription = prescription_serializer.save(customer=instance.customer, organization=self.context['request'].get_organization())
                instance.prescription = prescription  # Assigning the new prescription instance
        else:
            instance.prescription = None
        validated_data.pop('prescription', None)
        # Update other fields in the instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update inventory items if provided
        if inventory_items is not None:
            # Restore inventory quantities before deleting InvoiceItems
            existing_invoice_items = InvoiceItem.objects.filter(invoice=instance)
            for item in existing_invoice_items:
                inventory_item = item.inventory_item
                inventory_item.qty += item.quantity
                if inventory_item.qty > 0 and inventory_item.status == "Out of Stock":
                    inventory_item.status = "In Stock"
                inventory_item.save()

            # Delete existing InvoiceItems
            existing_invoice_items.delete()

            # Add new InvoiceItems and update inventory quantities
            total_price = 0
            for item_data in inventory_items:
                inventory_item = item_data['inventory_item']
                inventory_item = Inventory.objects.get(id=inventory_item.id)
                required_quantity = item_data['quantity']

                if inventory_item.qty < required_quantity:
                    raise serializers.ValidationError(f"Item {inventory_item.name} is out of stock or insufficient quantity.")

                InvoiceItem.objects.create(
                    invoice=instance,
                    inventory_item=inventory_item,
                    quantity=required_quantity,
                    sale_value=inventory_item.sale_value,
                    cost_value=inventory_item.cost_value,
                )

                inventory_item.qty -= required_quantity
                if inventory_item.qty == 0:
                    inventory_item.status = "Out of Stock"
                inventory_item.save()
                total_price += inventory_item.sale_value * required_quantity

            instance.total = total_price - instance.discount
            if instance.is_taxable:
                instance.total = instance.total + ((instance.tax_percentage / 100) * instance.total)

            # Update the InvoicePayment with payment_type="Advance" only if the advance amount has changed
            initial_advance = instance.advance
            if instance.advance != initial_advance:
                advance_payment = InvoicePayment.objects.filter(invoice=instance, payment_type="Advance").first()
                if advance_payment:
                    advance_payment.amount = instance.advance
                    advance_payment.save()
                else:
                    # Create a new advance payment if it doesn't exist
                    InvoicePayment.objects.create(
                        invoice=instance,
                        amount=instance.advance,
                        payment_type="Advance",
                        payment_mode=instance.advance_payment_mode,
                        remarks="Updated advance payment",
                        is_active=True
                    )

            instance.balance = instance.total - instance.advance
            if instance.balance < 0:
                raise ValueError("Invoice Balance calculation Error")
            instance.save()

        return instance


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
                "id",
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
        fields = ['inventory_item', 'sale_value', 'cost_value', 'quantity']


class InvoiceGetSerializer(serializers.ModelSerializer):
    class CustomerPartSerializer(serializers.ModelSerializer):
        class Meta:
            model = Customer
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

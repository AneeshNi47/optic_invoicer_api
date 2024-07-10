from django.core.management.base import BaseCommand
from invoices.models import Invoice, InvoicePayment, InvoiceItem


class Command(BaseCommand):
    help = 'Recalculate total and balance for all taxable invoices'

    def handle(self, *args, **kwargs):
        taxable_invoices = Invoice.objects.filter(is_taxable=True)

        for invoice in taxable_invoices:
            try:
                # Calculate the total from related InvoiceItem objects
                total_without_tax = sum(
                    item.sale_value * item.quantity for item in InvoiceItem.objects.filter(invoice=invoice)
                )
                total_without_tax = total_without_tax - invoice.discount
                # Add the tax
                tax_amount = (invoice.tax_percentage / 100) * total_without_tax
                new_total = total_without_tax + tax_amount

                # Calculate the total payments
                payments = InvoicePayment.objects.filter(invoice=invoice, is_active=True)
                total_payments = sum(payment.amount for payment in payments if payment.payment_type in ["Advance", "General"])

                # Calculate the new balance
                new_balance = new_total - total_payments

                # Update the invoice
                invoice.total = new_total
                invoice.balance = new_balance
                invoice.save()

                self.stdout.write(self.style.SUCCESS(f'Updated Invoice {invoice.invoice_number} - New Total: {new_total}, New Balance: {new_balance}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error updating Invoice {invoice.invoice_number}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Recalculation completed'))

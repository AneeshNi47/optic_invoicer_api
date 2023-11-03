from django.core.management.base import BaseCommand
from inventory.models import Inventory  # Adjust this import to match your project structure

class Command(BaseCommand):
    help = 'Generate SKUs for Inventory items that do not have one'

    def handle(self, *args, **options):
        items_without_sku = Inventory.objects.filter(SKU=None)
        for item in items_without_sku:
            item.SKU = item.generate_sku()  # Assuming your generate_sku method is defined on the Inventory model
            item.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully generated SKU {item.SKU} for item ID {item.id}'))

# tasks.py in one of your Django apps
from celery import shared_task
import logging
from io import StringIO
import csv
import requests
from django.apps import apps

@shared_task
def download_and_process_file(file_id, organization):
    InventoryCSV = apps.get_model('inventory', 'InventoryCSV')
    Inventory = apps.get_model('inventory', 'Inventory')

    try:
        inventory_csv = InventoryCSV.objects.get(id=file_id)
        if not inventory_csv.csv_file:
            raise ValueError("CSV file not found.")

        response = requests.get(inventory_csv.csv_file.url)
        response.raise_for_status()  # Raises HTTPError for bad requests (4xx or 5xx)

        file_content = response.content.decode('utf-8-sig')
        reader = csv.DictReader(StringIO(file_content))
        

        for row in reader:
            logging.info(f"Processing SKU: {row['store_sku']}")
            store_sku = row['store_sku']
            update_flag = row.pop('update', '').lower() == 'yes'
            row["organization"] = organization

            inventory_item, created = Inventory.objects.get_or_create(store_sku=store_sku, defaults=row)
            if not created and update_flag:
                Inventory.objects.filter(store_sku=store_sku).update(**row)

        inventory_csv.status = 'Completed'
        inventory_csv.save()

    except requests.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        inventory_csv.status = 'Error'
        inventory_csv.remarks = str(http_err)
        inventory_csv.save()
    except Exception as e:
        logging.error(f"Error: {e}")
        inventory_csv.status = 'Error'
        inventory_csv.remarks = str(e)
        inventory_csv.save()

# Replace print statements with logging for better output management
logging.basicConfig(level=logging.INFO)

        


import datetime
from django.apps import apps
from inventory.models import Inventory
from invoices.models import Invoice
from customers.models import Customer, Prescription

from django.db.models import Count, Sum, IntegerField
from django.db.models.functions import ExtractYear, ExtractMonth




def compute_statistics(model, organization, start_date, end_date, get_all):
        queryset = model.objects.filter(organization=organization)
        if not get_all:
              queryset = queryset.filter(created_on__range=(start_date, end_date))

        queryset = queryset.annotate(year=ExtractYear('created_on'),month=ExtractMonth('created_on')).values(
            'year', 'month')
        
        if model == Customer or model == Prescription:
            queryset = queryset.annotate(count=Count('id')).order_by('year', 'month')
        else:
            queryset =  queryset.annotate(
            count=Count('id'), 
            value=Sum('total' if model == Invoice else 'sale_value' if model == Inventory else None)
        ).order_by('year', 'month')
        
        return queryset

def compute_reports(organization, start_date=None, end_date=None, get_all=False):
        end_date = end_date or datetime.date.today()
        start_date = start_date or end_date - datetime.timedelta(days=5 * 30)

        invoice_stats = compute_statistics(Invoice, organization, start_date, end_date,get_all)
        inventory_stats = compute_statistics(Inventory, organization, start_date, end_date,get_all)
        customer_stats = compute_statistics(Customer, organization, start_date, end_date,get_all)
        prescription_stats = compute_statistics(Prescription, organization, start_date, end_date,get_all)

        # Convert stats to required format
        invoice_statistics = [{'year': stat['year'], 'month': stat['month'], 'count': stat['count'], 'value': float(stat['value'])} for stat in invoice_stats]
        inventory_statistics = [{'year': stat['year'], 'month': stat['month'], 'count': stat['count'], 'value': float(stat['value'])} for stat in inventory_stats]
        customer_statistics = [{'year': stat['year'], 'month': stat['month'], 'value': stat['count']} for stat in customer_stats]
        prescription_statistics = [{'year': stat['year'], 'month': stat['month'], 'value': stat['count']} for stat in prescription_stats]

        report_data = {
            "total_inventory": Inventory.objects.filter(organization=organization.id).count(),
            "inventory_statistics": inventory_statistics,
            "total_invoices": Invoice.objects.filter(organization=organization.id).count(),
            "invoice_statistics": invoice_statistics,
            "total_customers": Customer.objects.filter(organization=organization.id).count(),
            "customer_statistics": customer_statistics,
            "total_prescriptions": Prescription.objects.filter(organization=organization.id).count(),
            "prescription_statistics": prescription_statistics,
        }

        return report_data


def get_model_object(model_name):
    model_app_dict ={
            "Invoice": "invoices",
            "InvoiceItem": "invoices",
            "InvoicePayment": "invoices",
            "Customer":"customers",
            "Prescription":"customers",
            "Inventory":"inventory",
            "InventoryCSV":"inventory",
            "Organization":"organizations",
            "Payment":"organizations",
            "Subscription":"organizations",
            "Staff":"staff",
            "Staff":"staff",
      }
    app_label = model_app_dict.get(model_name)
    try:
        model = apps.get_model(app_label, model_name)
        return model
    except Exception as e:
         print(e)
         return None
    

def convert_date_request_to_start_end_dates(date_request_string):
    try:
        return date_request_dict.get(date_request_string)
    except Exception as e:
         print(e)
         return None 


def get_this_month_start_end_date():
    end_date = datetime.date.today()
    first_day_of_month = end_date.replace(day=1)
    return first_day_of_month,end_date


def get_start_date_end_date_previous_month():
    today = datetime.date.today()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - datetime.timedelta(days=1)
    first_day_of_previous_month = last_day_of_previous_month.replace(day=1)
    return first_day_of_previous_month, last_day_of_previous_month

date_request_dict={
         "this_month": get_this_month_start_end_date(),
         "last_month":get_start_date_end_date_previous_month()
    }
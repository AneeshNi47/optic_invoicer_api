

import datetime
from django.utils import timezone
from django.apps import apps
from .models import Subscription
from inventory.models import Inventory
from invoices.models import Invoice
from customers.models import Customer, Prescription
import random
import string
from django.db.models import Count, Sum
from django.db.models.functions import ExtractYear, ExtractMonth


def generate_random_password(length):
    if length < 8:
        raise ValueError("Password length should be at least 8 characters")

    letters = string.ascii_letters  # upper and lowercase letters
    digits = string.digits          # numbers
    special_chars = string.punctuation  # special character
    all_chars = letters + digits + special_chars

    password = [
        random.choice(letters),
        random.choice(digits),
        random.choice(special_chars)
    ]
    password += [random.choice(all_chars) for _ in range(length - 3)]
    random.shuffle(password)
    return ''.join(password)


def compute_statistics(model, organization, start_date, end_date, get_all):
    queryset = model.objects.filter(organization=organization)
    if not get_all:
        queryset = queryset.filter(created_on__range=(start_date, end_date))

    queryset = queryset.annotate(year=ExtractYear('created_on'), month=ExtractMonth('created_on')).values(
        'year', 'month')

    if model == Customer or model == Prescription:
        queryset = queryset.annotate(count=Count('id')).order_by('year', 'month')
    else:
        queryset = queryset.annotate(
            count=Count('id'),
            value=Sum('total' if model == Invoice else 'sale_value' if model == Inventory else None)
        ).order_by('year', 'month')

    return queryset


def compute_reports(organization, start_date=None, end_date=None, get_all=False):
    end_date = end_date or datetime.date.today()
    start_date = start_date or end_date - datetime.timedelta(days=5 * 30)

    invoice_stats = compute_statistics(Invoice, organization, start_date, end_date, get_all)
    inventory_stats = compute_statistics(Inventory, organization, start_date, end_date, get_all)
    customer_stats = compute_statistics(Customer, organization, start_date, end_date, get_all)
    prescription_stats = compute_statistics(Prescription, organization, start_date, end_date, get_all)

    # Convert stats to required format
    invoice_statistics = [{'year': stat['year'], 'month': stat['month'], 'count': stat['count'], 'value': float(stat['value'])} for stat in invoice_stats]
    inventory_statistics = [{'year': stat['year'], 'month': stat['month'], 'count': stat['count'], 'value': float(stat['value'])} for stat in inventory_stats]
    customer_statistics = [{'year': stat['year'], 'month': stat['month'], 'count': stat['count']} for stat in customer_stats]
    prescription_statistics = [{'year': stat['year'], 'month': stat['month'], 'count': stat['count']} for stat in prescription_stats]

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
    model_app_dict = {
        "Invoice": "invoices",
        "InvoiceItem": "invoices",
        "InvoicePayment": "invoices",
        "Customer": "customers",
        "Prescription": "customers",
        "Inventory": "inventory",
        "InventoryCSV": "inventory",
        "Organization": "organizations",
        "Payment": "organizations",
        "Subscription": "organizations",
        "Staff": "staff",
        "Staff": "staff",
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
    return first_day_of_month, end_date


def get_this_year_start_end_date():
    current_date = datetime.date.today()
    start_date = datetime.date(current_date.year, 1, 1)  # January 1st of the current year
    end_date = datetime.date(current_date.year, 12, 31)  # December 31st of the current year
    return start_date, end_date


def get_start_date_end_date_previous_month():
    today = datetime.date.today()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - datetime.timedelta(days=1)
    first_day_of_previous_month = last_day_of_previous_month.replace(day=1)
    return first_day_of_previous_month, last_day_of_previous_month


def get_this_week_start_end_date():
    current_date = datetime.date.today()
    start_date = current_date - datetime.timedelta(days=current_date.weekday())
    end_date = start_date + datetime.timedelta(days=6)
    return start_date, end_date


def get_last_year_start_end_date():
    current_year = datetime.date.today().year
    last_year = current_year - 1
    start_date = datetime.date(last_year, 1, 1)
    end_date = datetime.date(last_year, 12, 31)
    return start_date, end_date


def get_all_time_start_end_date():
    start_date = datetime.date(2020, 1, 1)  # Fixed start date
    end_date = datetime.date.today()  # Today's date
    return start_date, end_date


date_request_dict = {
    "all_time": get_all_time_start_end_date(),
    "this_year": get_this_year_start_end_date(),
    "this_week": get_this_week_start_end_date(),
    "this_month": get_this_month_start_end_date(),
    "last_month": get_start_date_end_date_previous_month(),
    "last_year": get_last_year_start_end_date()
}


def check_create_invoice_permission(organization):
    latest_subscription = Subscription.objects.filter(
        organization_id=organization.id,
        is_active=True
    ).order_by('-created_on').first()
    today = timezone.now().date()
    trial_start_date = latest_subscription.trial_start_date.date() if latest_subscription.trial_start_date else None
    trial_end_date = latest_subscription.trial_end_date.date() if latest_subscription.trial_end_date else None

    create_invoice_permission = (
        trial_start_date <= today <= trial_end_date
        if trial_start_date and trial_end_date
        else False
    )
    return latest_subscription, create_invoice_permission

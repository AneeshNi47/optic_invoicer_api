# Generated by Django 4.2 on 2024-06-06 10:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wholesale', '0004_salesorderitems'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wholesaleinventory',
            name='preferred_vendor',
        ),
    ]
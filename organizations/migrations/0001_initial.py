# Generated by Django 4.2 on 2023-09-26 13:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('address_first_line', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
                ('secondary_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('primary_phone_mobile', models.CharField(max_length=20)),
                ('other_contact_numbers', models.TextField(blank=True, null=True)),
                ('phone_landline', models.CharField(blank=True, max_length=20, null=True)),
                ('logo', models.ImageField(upload_to='organization_logos/')),
                ('translation_required', models.BooleanField(default=False)),
                ('country', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=100)),
                ('post_box_number', models.CharField(blank=True, max_length=50, null=True)),
                ('services', models.TextField(blank=True, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='organizations_created', to=settings.AUTH_USER_MODEL)),
                ('owner', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='owned_organization', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='organizations_updated', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]



from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            field=models.CharField(choices=[('Lens', 'Lens'), ('Frames', 'Frames'), ('Other', 'Other')], default='Lens', max_length=15),

        ),
    ]

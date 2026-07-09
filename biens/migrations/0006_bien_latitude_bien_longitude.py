# Generated manually to add GPS coordinates to Bien

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('biens', '0005_bien_meuble_bien_piscine_bien_proximite_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bien',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='bien',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]

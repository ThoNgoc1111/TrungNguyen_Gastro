# Generated by Django 2.2.14 on 2024-11-12 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20190630_1408'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='category',
            field=models.CharField(choices=[('PC', 'Packaged Coffee'), ('GS', 'Gift Suggestions'), ('BI', 'Branded Items'), ('PB', 'Precious Bookcase'), ('PP', 'Partner Products')], max_length=2),
        ),
    ]

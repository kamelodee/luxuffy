# Generated by Django 5.1.3 on 2024-12-17 12:06

from django.db import migrations
import uuid

def gen_uuid(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for row in Product.objects.all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=['uuid'])

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0018_auto_20241217_1201'),
    ]

    operations = [
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop),
    ]

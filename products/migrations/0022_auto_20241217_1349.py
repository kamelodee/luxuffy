# Generated by Django 5.1.3 on 2024-12-17 13:49

from django.db import migrations, models
import uuid

def gen_uuid(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    db_alias = schema_editor.connection.alias
    for row in Product.objects.using(db_alias).all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=['uuid'])

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0021_auto_20241217_1211'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, unique=True),
        ),
        migrations.RunPython(gen_uuid),
    ]

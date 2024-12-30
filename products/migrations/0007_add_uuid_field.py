from django.db import migrations, models
import uuid

def gen_uuid(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for row in Product.objects.all():
        row.uuid_field = uuid.uuid4()
        row.save(update_fields=['uuid_field'])

class Migration(migrations.Migration):
    dependencies = [
        ('products', '0006_alter_product_id'),
    ]

    operations = [
        # Add UUID field
        migrations.AddField(
            model_name='product',
            name='uuid_field',
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        # Generate UUID values for existing records
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop),
        # Make UUID field non-nullable
        migrations.AlterField(
            model_name='product',
            name='uuid_field',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]

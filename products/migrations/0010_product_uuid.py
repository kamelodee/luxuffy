from django.db import migrations, models
import uuid

def gen_uuid(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for row in Product.objects.all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=['uuid'])

class Migration(migrations.Migration):
    dependencies = [
        ('products', '0009_merge_0007_merge_20241217_1037_0008_switch_to_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='product',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]

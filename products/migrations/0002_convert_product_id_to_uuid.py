from django.db import migrations, models
import uuid

def gen_uuid(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for row in Product.objects.all():
        row.new_id = uuid.uuid4()
        row.save(update_fields=['new_id'])

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),  # adjust this to your last migration
    ]

    operations = [
        # Add a new UUID field allowing null values initially
        migrations.AddField(
            model_name='Product',
            name='new_id',
            field=models.UUIDField(null=True, blank=True),
        ),
        
        # Generate UUIDs for existing rows
        migrations.RunPython(gen_uuid),
        
        # Remove null constraint from new_id field
        migrations.AlterField(
            model_name='Product',
            name='new_id',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
        
        # Remove the old id field
        migrations.RemoveField(
            model_name='Product',
            name='id',
        ),
        
        # Rename new_id to id
        migrations.RenameField(
            model_name='Product',
            old_name='new_id',
            new_name='id',
        ),
        
        # Add primary key constraint to id field
        migrations.AlterField(
            model_name='Product',
            name='id',
            field=models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False),
        ),
    ]

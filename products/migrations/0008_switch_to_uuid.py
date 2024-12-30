from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    dependencies = [
        ('products', '0007_add_uuid_field'),
    ]

    operations = [
        # Remove the primary key from id field
        migrations.AlterField(
            model_name='product',
            name='id',
            field=models.BigIntegerField(),
        ),
        # Make uuid_field the primary key
        migrations.AlterField(
            model_name='product',
            name='uuid_field',
            field=models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False),
        ),
        # Remove old id field
        migrations.RemoveField(
            model_name='product',
            name='id',
        ),
        # Rename uuid_field to id
        migrations.RenameField(
            model_name='product',
            old_name='uuid_field',
            new_name='id',
        ),
    ]

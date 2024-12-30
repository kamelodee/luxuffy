from django.db import migrations, models
import uuid

def gen_uuid(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    db_alias = schema_editor.connection.alias
    for product in Product.objects.using(db_alias).all():
        Product.objects.using(db_alias).filter(id=product.id).update(temp_id=uuid.uuid4())

class Migration(migrations.Migration):
    dependencies = [
        ('products', '0005_alter_product_id_alter_product_product_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='temp_id',
            field=models.UUIDField(null=True),
        ),
        migrations.RunPython(gen_uuid),
        migrations.RemoveField(
            model_name='product',
            name='id',
        ),
        migrations.RenameField(
            model_name='product',
            old_name='temp_id',
            new_name='id',
        ),
        migrations.AlterField(
            model_name='product',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False),
        ),
    ]

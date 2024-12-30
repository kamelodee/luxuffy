from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('products', '0010_product_uuid'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
            ALTER TABLE products_product 
                DROP CONSTRAINT products_product_pkey CASCADE;
            ALTER TABLE products_product
                ADD PRIMARY KEY (uuid);
            ALTER TABLE products_product
                DROP COLUMN id;
            ALTER TABLE products_product
                RENAME COLUMN uuid TO id;
            ''',
            reverse_sql='''
            ALTER TABLE products_product
                DROP CONSTRAINT products_product_pkey CASCADE;
            ALTER TABLE products_product
                ADD COLUMN id SERIAL PRIMARY KEY;
            ALTER TABLE products_product
                RENAME COLUMN id TO uuid;
            '''
        ),
    ]

# Generated by Django 5.1.2 on 2024-12-05 11:32

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
        ('vendors', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LiveStream',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='streams/thumbnails/')),
                ('stream_key', models.CharField(max_length=100, unique=True)),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('live', 'Live'), ('ended', 'Ended'), ('cancelled', 'Cancelled')], default='scheduled', max_length=20)),
                ('scheduled_start', models.DateTimeField()),
                ('actual_start', models.DateTimeField(blank=True, null=True)),
                ('actual_end', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('allow_replay', models.BooleanField(default=True)),
                ('replay_url', models.URLField(blank=True, null=True)),
                ('viewer_count', models.PositiveIntegerField(default=0)),
                ('peak_viewers', models.PositiveIntegerField(default=0)),
                ('total_views', models.PositiveIntegerField(default=0)),
                ('total_likes', models.PositiveIntegerField(default=0)),
                ('total_comments', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='live_streams', to='vendors.vendor')),
            ],
            options={
                'ordering': ['-scheduled_start'],
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='video_shop_orders', to='products.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='video_shop_orders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='StreamAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_duration', models.DurationField(blank=True, null=True)),
                ('average_viewers', models.PositiveIntegerField(default=0)),
                ('engagement_rate', models.FloatField(default=0)),
                ('revenue', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('stream', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analytics', to='chat_to_shop.livestream')),
            ],
        ),
        migrations.CreateModel(
            name='StreamInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interaction_type', models.CharField(choices=[('view', 'View'), ('like', 'Like'), ('comment', 'Comment'), ('product_click', 'Product Click')], max_length=20)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('comment_text', models.TextField(blank=True, null=True)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.product')),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='chat_to_shop.livestream')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='StreamProductAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('views', models.PositiveIntegerField(default=0)),
                ('clicks', models.PositiveIntegerField(default=0)),
                ('purchases', models.PositiveIntegerField(default=0)),
                ('revenue', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('analytics', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat_to_shop.streamanalytics')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
            ],
            options={
                'unique_together': {('analytics', 'product')},
            },
        ),
        migrations.AddField(
            model_name='streamanalytics',
            name='products_shown',
            field=models.ManyToManyField(through='chat_to_shop.StreamProductAnalytics', to='products.product'),
        ),
        migrations.CreateModel(
            name='VideoContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('video_file', models.FileField(upload_to='videos/content/')),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='videos/thumbnails/')),
                ('duration', models.DurationField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('view_count', models.PositiveIntegerField(default=0)),
                ('interaction_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='videos', to='vendors.vendor')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProductTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DurationField()),
                ('position_x', models.FloatField()),
                ('position_y', models.FloatField()),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='video_tags', to='products.product')),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_tags', to='chat_to_shop.videocontent')),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
    ]

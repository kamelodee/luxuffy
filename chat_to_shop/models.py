from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from vendors.models import Vendor
from products.models import Product

class VideoContent(models.Model):
    """Model for vendor product showcase videos"""
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to='videos/content/')
    thumbnail = models.ImageField(upload_to='videos/thumbnails/', null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    
    # Status and visibility
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    interaction_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.vendor.store_name} - {self.title}"

class ProductTag(models.Model):
    """Model for product tags in videos"""
    
    video = models.ForeignKey(VideoContent, on_delete=models.CASCADE, related_name='product_tags')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='video_tags')
    timestamp = models.DurationField()  # When the product appears in the video
    position_x = models.FloatField()  # X coordinate (0-100)
    position_y = models.FloatField()  # Y coordinate (0-100)
    
    class Meta:
        ordering = ['timestamp']
        
    def __str__(self):
        return f"{self.product.name} at {self.timestamp}"

class LiveStream(models.Model):
    """Model for vendor live streaming sessions"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='live_streams')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='streams/thumbnails/', null=True, blank=True)
    
    # Stream details
    stream_key = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    scheduled_start = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Stream settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    allow_replay = models.BooleanField(default=True)
    replay_url = models.URLField(blank=True, null=True)
    
    # Analytics
    viewer_count = models.PositiveIntegerField(default=0)
    peak_viewers = models.PositiveIntegerField(default=0)
    total_views = models.PositiveIntegerField(default=0)
    total_likes = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_start']
        
    def __str__(self):
        return f"{self.vendor.store_name} - {self.title}"

class StreamInteraction(models.Model):
    """Model for tracking user interactions during live streams"""
    
    INTERACTION_TYPES = [
        ('view', 'View'),
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('product_click', 'Product Click'),
    ]
    
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    comment_text = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.stream.title} - {self.interaction_type} at {self.timestamp}"

class StreamAnalytics(models.Model):
    """Model for aggregated stream analytics"""
    
    stream = models.OneToOneField(LiveStream, on_delete=models.CASCADE, related_name='analytics')
    total_duration = models.DurationField(null=True, blank=True)
    average_viewers = models.PositiveIntegerField(default=0)
    engagement_rate = models.FloatField(default=0)  # Calculated as (likes + comments) / views
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Product performance
    products_shown = models.ManyToManyField(Product, through='StreamProductAnalytics')
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics for {self.stream.title}"

class StreamProductAnalytics(models.Model):
    """Model for tracking product performance during streams"""
    
    analytics = models.ForeignKey(StreamAnalytics, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    views = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    purchases = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['analytics', 'product']
        
    def __str__(self):
        return f"{self.product.name} performance in {self.analytics.stream.title}"

class Order(models.Model):
    """Model for user product orders"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_shop_orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='video_shop_orders')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.product.name} by {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.product.price * self.quantity
        super().save(*args, **kwargs)

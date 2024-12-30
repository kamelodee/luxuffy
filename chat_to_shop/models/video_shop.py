from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()

class VideoContent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to='videos/')
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True)
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE)
    category = models.ForeignKey('products.Category', on_delete=models.SET_NULL, null=True)
    duration = models.IntegerField(help_text='Duration in seconds')
    view_count = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['vendor']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.title

class ProductTag(models.Model):
    video = models.ForeignKey(VideoContent, on_delete=models.CASCADE, related_name='product_tags')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    position_x = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='X position in percentage (0-100)'
    )
    position_y = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Y position in percentage (0-100)'
    )
    timestamp = models.IntegerField(
        help_text='Timestamp in seconds when the product appears',
        null=True, blank=True
    )

    class Meta:
        unique_together = ['video', 'product', 'timestamp']

class LiveStream(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE)
    thumbnail = models.ImageField(upload_to='stream_thumbnails/', blank=True, null=True)
    category = models.ForeignKey('products.Category', on_delete=models.SET_NULL, null=True)
    is_live = models.BooleanField(default=False)
    viewer_count = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    featured_products = models.ManyToManyField('products.Product', related_name='featured_in_streams')
    stream_key = models.CharField(max_length=100, unique=True)
    chat_enabled = models.BooleanField(default=True)
    qa_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['-started_at']),
            models.Index(fields=['vendor']),
            models.Index(fields=['is_live']),
        ]

    def __str__(self):
        return f"{self.vendor.name} - {self.title}"

    def start_stream(self):
        if not self.is_live:
            self.is_live = True
            self.started_at = timezone.now()
            self.save()

    def end_stream(self):
        if self.is_live:
            self.is_live = False
            self.ended_at = timezone.now()
            self.save()

    def update_viewer_count(self, count):
        self.viewer_count = count
        self.save()

class StreamInteraction(models.Model):
    INTERACTION_TYPES = [
        ('comment', 'Comment'),
        ('question', 'Question'),
        ('reaction', 'Reaction'),
    ]

    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='interactions')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['stream', 'created_at']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.interaction_type} on {self.stream.title}"

class StreamAnalytics(models.Model):
    stream = models.OneToOneField(LiveStream, on_delete=models.CASCADE, related_name='analytics')
    peak_viewers = models.IntegerField(default=0)
    total_views = models.IntegerField(default=0)
    average_watch_time = models.FloatField(default=0)
    engagement_rate = models.FloatField(default=0)
    product_clicks = models.JSONField(default=dict)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Analytics for {self.stream.title}"

    def update_analytics(self, current_viewers, watch_time):
        self.peak_viewers = max(self.peak_viewers, current_viewers)
        self.total_views += 1
        self.average_watch_time = (self.average_watch_time * (self.total_views - 1) + watch_time) / self.total_views
        self.save()

    def record_product_click(self, product_id):
        if str(product_id) in self.product_clicks:
            self.product_clicks[str(product_id)] += 1
        else:
            self.product_clicks[str(product_id)] = 1
        self.save()

    def update_revenue(self, amount):
        self.revenue += amount
        self.save()

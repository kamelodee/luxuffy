from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    """Comprehensive model for product categories"""
    
    # Basic Information
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True, help_text="Description of the category")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    image = models.ImageField(upload_to='imags/', null=True, blank=True)
    
    # Display Order and Visibility
    is_active = models.BooleanField(default=True, help_text="Is the category active and visible to customers?")
    display_order = models.PositiveIntegerField(default=0, help_text="Order for displaying categories")
    
    # SEO and Marketing
    meta_title = models.CharField(max_length=150, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)
    seo_url = models.CharField(max_length=255, blank=True, null=True, help_text="Custom SEO-friendly URL")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['name']),
        ]

    def save(self, *args, **kwargs):
        # Automatically generate slug if not set
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name

    def get_full_path(self):
        """Recursively get the full category path for nested categories."""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name

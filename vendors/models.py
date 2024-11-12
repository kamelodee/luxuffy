from django.db import models
from django.utils.text import slugify

from accounts.models import User
# Create your models here.
class Vendor(models.Model):
    """Model for a vendor selling products on the platform"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor')
    business_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.business_name)
        super().save(*args, **kwargs)
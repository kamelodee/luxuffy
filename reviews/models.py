from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from accounts.models import User


class Review(models.Model):
    """Model for user reviews for vendors or products."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)  # Links to either Vendor or Product
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')  # Dynamic link to Vendor or Product
    rating = models.PositiveSmallIntegerField(default=1)  # Rating (e.g., 1-5 stars)
    title = models.CharField(max_length=255, null=True, blank=True)  # Optional title for the review
    comment = models.TextField()  # The review text
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Review status
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review by {self.user} on {self.content_object} - {self.get_status_display()}"


class ReviewImage(models.Model):
    """Model for images uploaded with reviews."""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for review {self.review.id}"

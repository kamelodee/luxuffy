from django.db import models
from django.utils import timezone
from accounts.models import User
from orders.models import Order

# Create your models here.

class Payment(models.Model):
    """Model for tracking payments"""
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=200, unique=True)
    paystack_reference = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=50, default='card')
    currency = models.CharField(max_length=3, default='NGN')
    metadata = models.JSONField(default=dict, blank=True)
    gateway_response = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.reference} for Order #{self.order.id}"


class PaymentRefund(models.Model):
    """Model for tracking payment refunds"""
    REFUND_STATUS = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed')
    )

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=200, unique=True)
    paystack_reference = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=REFUND_STATUS, default='pending')
    reason = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    gateway_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund {self.reference} for Payment {self.payment.reference}"

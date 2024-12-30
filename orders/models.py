from django.db import models
from accounts.models import User
from products.models import Product

from django.db import models
from accounts.models import User
from products.models import Product

class Order(models.Model):
    """Model for a customer order"""
    # User and order-related fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    products = models.ManyToManyField(Product, through='OrderItem')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total before tax and discounts")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Shipping and delivery information
    shipping_address = models.CharField(max_length=255, null=True)
    billing_address = models.CharField(max_length=255, null=True)
    shipping_method = models.CharField(max_length=50, choices=[
        ('standard', 'Standard Shipping'),
        ('express', 'Express Shipping'),
        ('overnight', 'Overnight Shipping')
    ], default='standard')
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    estimated_delivery_date = models.DateField(blank=True, null=True)

    # Latitude and Longitude for shipping and billing addresses
    shipping_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    shipping_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    billing_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    billing_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Order status tracking
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned')
    ], default='pending')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    tracking_url = models.URLField(blank=True, null=True, help_text="URL for tracking the shipment")
    
    # Payment information
    payment_method = models.CharField(max_length=50, choices=[
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('bank_transfer', 'Bank Transfer')
    ], default='credit_card')
    payment_status = models.CharField(max_length=20, choices=[
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded')
    ], default='unpaid')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Date fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} by {self.user.username} - {self.status}"


class OrderItem(models.Model):
    """Model for an item in a customer order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Price * Quantity", default=1)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Discount applied on item")
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Tax applied on item")

    # Date fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order #{self.order.id}"


from django.db import models
from django.utils import timezone
from accounts.models import User
from products.models import Product


class Cart(models.Model):
    """Model for a user's shopping cart"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    products = models.ManyToManyField(Product, through='CartItem')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Cart of {self.user.username}"


class CartItem(models.Model):
    """Model for an item in a user's shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    # Price and discount fields
    price = models.DecimalField(max_digits=12, decimal_places=2,default=5, help_text="Unit price at the time added to cart")
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Discount on item")
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Tax on item")
    total_price = models.DecimalField(max_digits=12, decimal_places=2,default=1, help_text="(Price - Discount) * Quantity + Tax")
    
    # Availability and status tracking
    is_available = models.BooleanField(default=True, help_text="Indicates if the item is still in stock")
    is_wishlist_item = models.BooleanField(default=False, help_text="Indicates if the item is saved for later")
    
    # Auditing fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'product')  # Ensures each product is only in the cart once

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Cart of {self.cart.user.username}"

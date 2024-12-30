from django.db import models
from django.core.validators import (
    MinLengthValidator, 
    RegexValidator, 
    MaxLengthValidator,
    URLValidator
)
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.models import User


class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    """
    Model representing a seller profile for users with enhanced validation and organization.
    Includes business details, verification, contact information, and shipping details.
    """
    
    # Status Choices
    ACCOUNT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('suspended', 'Suspended'),
        ('deactivated', 'Deactivated'),
    ]

    VERIFICATION_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    # Payment Type Choices
    PAYMENT_TYPE_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('both', 'Both Bank Transfer and Mobile Money'),
        ('none', 'No Payment Method Set')
    ]

    # Basic Information
   

    # Business Information
    business_name = models.CharField(max_length=255, unique=True)
    business_type = models.CharField(
        max_length=100, 
        choices=[('individual', 'Individual'), ('company', 'Company')],
        default='individual'
    )
    store_name = models.CharField(max_length=255, unique=True)
    
    # Images
    logo_url = models.CharField(max_length=255, blank=True, null=True)
    banner_url = models.CharField(max_length=255, blank=True, null=True)

    # Verification
    verification_status = models.CharField(
        max_length=10,
        choices=VERIFICATION_CHOICES,
        default='pending',
        help_text="Current verification status of the vendor",
        blank=True,
        null=True
    )
    account_status = models.CharField(
        max_length=20,
        choices=ACCOUNT_STATUS_CHOICES,
        default='pending',
        blank=True,
        null=True
    )
    verification_date = models.DateTimeField(blank=True, null=True)
    verification_notes = models.TextField(blank=True, null=True)

    # Personal/Business Documentation
    full_name = models.CharField(max_length=15, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    id_type = models.CharField(max_length=15, blank=True, null=True)
    id_number = models.CharField(max_length=15, blank=True, null=True)
    tin_number = models.CharField(max_length=15, blank=True, null=True)
    id_front_url = models.CharField(max_length=255, blank=True, null=True)
    id_back_url = models.CharField(max_length=255, blank=True, null=True)
    
    # Contact Information
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # Business Address
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    locality = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default="Ghana")
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    # Shipping Address
    ship_from_address1 = models.CharField(max_length=255, blank=True, null=True)
    ship_from_address2 = models.CharField(max_length=255, blank=True, null=True)
    ship_from_city = models.CharField(max_length=100, blank=True, null=True)
    ship_from_locality = models.CharField(max_length=100, blank=True, null=True)
    ship_from_region = models.CharField(max_length=100, blank=True, null=True)
    ship_from_country = models.CharField(max_length=100, blank=True, null=True)

    # Return Address
    return_address1 = models.CharField(max_length=255, blank=True, null=True)
    return_address2 = models.CharField(max_length=255, blank=True, null=True)
    return_city = models.CharField(max_length=100, blank=True, null=True)
    return_locality = models.CharField(max_length=100, blank=True, null=True)
    return_region = models.CharField(max_length=100, blank=True, null=True)
    return_country = models.CharField(max_length=100, default="Ghana",blank=True, null=True)

    # Location Data
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    # Payment Information
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        help_text="Select the payment method(s) you want to accept",
        blank=True,
        null=True

    )
    account_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Bank account number (required if payment type includes bank transfer)"
    )
    mobile_money_number = models.CharField(
    max_length=100,
    blank=True,
    null=True
)
    phone_number = models.CharField(
    max_length=16,
    blank=True,
    null=True
)
    phone_number2 = models.CharField(
    max_length=16,
    blank=True,
    null=True
)

    # SEO Fields
    meta_title = models.CharField(
        max_length=70,
        null=True,
        blank=True,
        help_text="SEO-friendly title (max 70 characters)"
    )
    meta_description = models.TextField(
        null=True,
        blank=True,
        help_text="SEO-friendly description (max 160 characters)"
    )
    meta_keywords = models.TextField(
        null=True,
        blank=True,
        help_text="Comma-separated keywords for SEO"
    )
    canonical_url = models.URLField(
        null=True,
        blank=True,
        help_text="Canonical URL for SEO"
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store_name']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['account_status']),
            models.Index(fields=['payment_type']),
            models.Index(fields=['ship_from_city']),
            models.Index(fields=['return_city']),
        ]

    def clean(self):
        """Validate payment information based on payment type."""
        from django.core.exceptions import ValidationError
        
        if self.payment_type in ['bank_transfer', 'both'] and not self.account_number:
            raise ValidationError({
                'account_number': 'Bank account number is required for bank transfer payment type.'
            })
            
        if self.payment_type in ['mobile_money', 'both'] and not self.mobile_money_number:
            raise ValidationError({
                'mobile_money_number': 'Mobile money number is required for mobile money payment type.'
            })

    def save(self, *args, **kwargs):
        """Generate unique slug for the store name if not provided."""
        if not self.store_name:
            self.store_name = slugify(self.business_name)
        
        # Call clean method
        self.clean()
        
        super().save(*args, **kwargs)

    def use_business_address_for_shipping(self):
        """Copy business address to shipping address."""
        self.ship_from_address1 = self.address_line1
        self.ship_from_address2 = self.address_line2
        self.ship_from_city = self.city
        self.ship_from_locality = self.locality
        self.ship_from_region = self.region
        self.ship_from_country = self.country

    def use_business_address_for_returns(self):
        """Copy business address to return address."""
        self.return_address1 = self.address_line1
        self.return_address2 = self.address_line2
        self.return_city = self.city
        self.return_locality = self.locality
        self.return_region = self.region
        self.return_country = self.country

    @property
    def accepts_bank_transfer(self):
        """Check if vendor accepts bank transfer."""
        return self.payment_type in ['bank_transfer', 'both']

    @property
    def accepts_mobile_money(self):
        """Check if vendor accepts mobile money."""
        return self.payment_type in ['mobile_money', 'both']

    def get_shipping_address_display(self):
        """Return formatted shipping address."""
        return f"{self.ship_from_address1}, {self.ship_from_city}, {self.ship_from_region}, {self.ship_from_country}"

    def get_return_address_display(self):
        """Return formatted return address."""
        return f"{self.return_address1}, {self.return_city}, {self.return__region}, {self.return_country}"

    def __str__(self):
        return f"{self.business_name} (User: {self.user.username})"
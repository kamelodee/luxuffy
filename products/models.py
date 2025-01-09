from django.db import models
import uuid
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from categories.models import Category
from vendors.models import Vendor
from django.utils import timezone

# Brand Model
class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True, default='')
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

# Product Model
class Product(models.Model):
    """Comprehensive model for a product sold on the platform"""
    PRODUCT_TYPE_CHOICES = [
        ('simple', 'Simple Product'),
        ('variable', 'Variable Product'),
        ('digital', 'Digital Product'),
    ]
    PRODUCT_STATUS = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )

    # Basic Information
    id = models.BigAutoField(primary_key=True)
     # Initially allow null
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, default='')
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='simple')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    tags = models.ManyToManyField('Tag', related_name='products', blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    favorites = models.ManyToManyField('auth.User', related_name='favorite_products', blank=True)
    
    # Pricing and SKU
    price = models.DecimalField(max_digits=12, decimal_places=2, default=5)
    compare_at_price = models.DecimalField(max_digits=12, decimal_places=2, default=5)
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, 
                                       help_text="Discounted price, if available")
    sku = models.CharField(max_length=20, unique=True, blank=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    
    # Media
    video = models.URLField(blank=True, null=True, help_text="Product demonstration video URL (optional)")
    
    # Inventory and Availability
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, help_text="Is product active and available for purchase?")
    is_featured = models.BooleanField(default=False, help_text="Is this a featured product?")
    available_from = models.DateTimeField(blank=True, null=True)
    available_to = models.DateTimeField(blank=True, null=True)
    
    # Physical Product Attributes (for simple and variable products)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, 
                               help_text="Weight in kilograms")
    dimensions = models.CharField(max_length=50, blank=True, null=True, 
                                help_text="Dimensions (L x W x H) in cm")
    
    # Digital Product Attributes
    digital_file = models.FileField(upload_to='digital_products/', null=True, blank=True,
                                  help_text="Uploadable file for digital products")
    download_limit = models.PositiveIntegerField(null=True, blank=True,
                                               help_text="Number of times the file can be downloaded")
    download_expiry = models.PositiveIntegerField(null=True, blank=True,
                                                help_text="Number of days before the download link expires")
    
    # SEO and Marketing
    meta_title = models.CharField(max_length=70, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # New field for session products
    is_session = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['product_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        return self.name

    def get_primary_image(self):
        """Returns the primary image for this product or None if no images exist."""
        return self.images.filter(is_primary=True).first()

    def save(self, *args, **kwargs):
       
        if not self.slug:
            self.slug = slugify(self.name)
            # Make slug unique
            original_slug = self.slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        if not self.sku:
            base_sku = uuid.uuid4().hex[:8]
            counter = 1
            temp_sku = base_sku
            
            while Product.objects.filter(sku=temp_sku).exists():
                temp_sku = f"{base_sku}-{counter}"
                counter += 1
            
            self.sku = temp_sku
            
        super().save(*args, **kwargs)

    def clean(self):
        if self.product_type == 'digital':
            if not self.digital_file:
                raise ValidationError("Digital products must have a digital file.")
            # Clear physical attributes for digital products
            self.weight = None
            self.dimensions = None
            self.stock_quantity = None
        elif self.product_type == 'variable':
            # For variable products, stock is managed at variant level
            self.stock_quantity = None
        else:  # simple product
            # Clear digital attributes for simple products
            self.digital_file = None
            self.download_limit = None
            self.download_expiry = None

# ProductImage Model
class ProductImage(models.Model):
    """Model for storing product images"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    alt_text = models.CharField(max_length=128, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'

    def __str__(self):
        return f'{self.product.name} - Image'

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Set all other images of this product to not primary
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).update(is_primary=False)
        super().save(*args, **kwargs)

# ProductVariant Model
class ProductVariant(models.Model):
    """Model for product variants (e.g., different sizes, colors)"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    name = models.CharField(max_length=100, default='Default Variant', help_text="Variant name (e.g., 'Small Blue')")
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    dimensions = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    material = models.CharField(max_length=50, blank=True, null=True)
    style = models.CharField(max_length=50, blank=True, null=True)
    variant_image = models.ImageField(upload_to='product_variants/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['product__name', 'name']
        unique_together = ('product', 'sku')

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def clean(self):
        if self.price and self.discount_price and self.discount_price >= self.price:
            raise ValidationError("Discount price must be less than regular price")

# ProductSpecification Model
class ProductSpecification(models.Model):
    """Model for storing product specifications"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='specifications'
    )
    specification_name = models.CharField(max_length=255)
    specification_value = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['specification_name']
        unique_together = ('product', 'specification_name')

    def __str__(self):
        return f"{self.product.name} - {self.specification_name}"

# Tag Model
class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

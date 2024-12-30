from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, HTML, Field
from .models import Vendor
from products.models import Product, ProductVariant

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'business_name', 'business_type', 'store_name', 'logo_url', 'banner_url',
            'full_name', 'email', 'phone_number', 'address_line1', 'address_line2',
            'city', 'locality', 'region', 'country', 'postal_code',
            'payment_type', 'account_number', 'mobile_money_number'
        ]
        widgets = {
            'business_type': forms.Select(attrs={'class': 'form-select'}),
            'logo_url': forms.FileInput(attrs={'class': 'form-control'}),
            'banner_url': forms.FileInput(attrs={'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.layout = Layout(
            # Store Information
            Div(
                HTML('<h5 class="mb-3">Store Information</h5>'),
                Row(
                    Column('business_name', css_class='form-group col-md-4'),
                    Column('business_type', css_class='form-group col-md-4'),
                    Column('store_name', css_class='form-group col-md-4'),
                    css_class='form-row'
                ),
                Row(
                    Column('logo', css_class='form-group col-md-6'),
                    Column('banner', css_class='form-group col-md-6'),
                    css_class='form-row'
                ),
                css_class='mb-4'
            ),
            
            # Contact Information
            Div(
                HTML('<h5 class="mb-3">Contact Information</h5>'),
                Row(
                    Column('full_name', css_class='form-group col-md-6'),
                    Column('email', css_class='form-group col-md-6'),
                    css_class='form-row'
                ),
                'phone_number',
                css_class='mb-4'
            ),
            
            # Address Information
            Div(
                HTML('<h5 class="mb-3">Address Information</h5>'),
                'address_line1',
                'address_line2',
                Row(
                    Column('city', css_class='form-group col-md-4'),
                    Column('locality', css_class='form-group col-md-4'),
                    Column('region', css_class='form-group col-md-4'),
                    css_class='form-row'
                ),
                Row(
                    Column('country', css_class='form-group col-md-6'),
                    Column('postal_code', css_class='form-group col-md-6'),
                    css_class='form-row'
                ),
                css_class='mb-4'
            ),
            
            # Payment Information
            Div(
                HTML('<h5 class="mb-3">Payment Information</h5>'),
                'payment_type',
                Div(
                    Row(
                        Column('account_number', css_class='form-group col-md-6'),
                        Column('mobile_money_number', css_class='form-group col-md-6'),
                        css_class='form-row'
                    ),
                    css_class='payment-fields'
                ),
                css_class='mb-4'
            ),
            
            Div(
                Submit('submit', 'Save Changes', css_class='btn btn-primary'),
                css_class='text-right'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        account_number = cleaned_data.get('account_number')
        mobile_money_number = cleaned_data.get('mobile_money_number')

        if payment_type in ['bank_transfer', 'both']:
            if not account_number:
                raise ValidationError('Bank account number is required for bank transfer payment type.')

        if payment_type in ['mobile_money', 'both']:
            if not mobile_money_number:
                self.add_error('mobile_money_number', 'Mobile money number is required for mobile money payment type.')

        return cleaned_data


class ProductForm(forms.ModelForm):
    PRODUCT_TYPE_CHOICES = [
        ('simple', 'Simple Product'),
        ('variable', 'Variable Product'),
    ]

    product_type = forms.ChoiceField(
        choices=PRODUCT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'select2',
            'id': 'product-type-select'
        })
    )

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'product_type', 'price', 'image',
            'is_active', 'stock_quantity', 'weight', 'dimensions', 'brand',
            'discount_price', 'barcode', 'meta_title', 'meta_description',
            'meta_keywords', 'is_featured', 'sku', 'compare_at_price', 'status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'select2', 'required': True}),
            'brand': forms.Select(attrs={'class': 'select2'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'required': True}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set required fields
        self.fields['name'].required = True
        self.fields['category'].required = True
        self.fields['price'].required = True
        self.fields['stock_quantity'].required = True
        self.fields['sku'].required = True
        
        # Add help text
        self.fields['sku'].help_text = 'Unique identifier for this product'
        self.fields['price'].help_text = 'Base price for simple products or minimum price for variable products'
        self.fields['stock_quantity'].help_text = 'Available quantity for simple products'
        
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.Select):
                self.fields[field].widget.attrs['class'] = 'select2'

    def clean(self):
        cleaned_data = super().clean()
        product_type = cleaned_data.get('product_type')
        price = cleaned_data.get('price')
        stock_quantity = cleaned_data.get('stock_quantity')

        if product_type == 'simple':
            if not price:
                self.add_error('price', 'Price is required for simple products')
            if stock_quantity is None:
                self.add_error('stock_quantity', 'Stock quantity is required for simple products')

        return cleaned_data


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['name', 'sku', 'price', 'stock_quantity', 'weight', 'dimensions', 'size', 'color', 'material']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Small Blue'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unique SKU for this variant'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'dimensions': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 10x20x30'
            }),
            'size': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Small, Medium, Large'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Blue, Red, Green'
            }),
            'material': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Cotton, Polyester'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['sku'].required = True
        self.fields['price'].required = True
        self.fields['stock_quantity'].required = True
        
        # Add help text
        self.fields['sku'].help_text = 'Unique identifier for this variant'
        self.fields['price'].help_text = 'Price for this specific variant'
        self.fields['stock_quantity'].help_text = 'Available quantity for this variant'

ProductVariantFormSet = forms.inlineformset_factory(
    Product,
    ProductVariant,
    form=ProductVariantForm,
    extra=1,
    can_delete=True,
    fields=['name', 'sku', 'price', 'stock_quantity', 'weight', 'dimensions', 'size', 'color', 'material']
)

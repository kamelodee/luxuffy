from django import forms
from .models import Product, ProductImage, ProductVariant, ProductSpecification, Brand, Tag

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['slug', 'created_at', 'updated_at', 'sku']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'meta_keywords': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'available_from': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'available_to': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Textarea, forms.CheckboxInput)):
                field.widget.attrs.update({'class': 'form-control'})
        self.fields['tags'].widget.attrs.update({'class': 'form-control select2-multiple', 'multiple': 'multiple'})
        self.fields['product_type'].widget.attrs.update({'class': 'form-control product-type-select'})
        self.fields['category'].queryset = self.fields['category'].queryset.order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        product_type = cleaned_data.get('product_type')
        digital_file = cleaned_data.get('digital_file')

        if product_type == 'digital' and not digital_file:
            raise forms.ValidationError("Digital products must have a digital file.")
        return cleaned_data

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['alt_text', 'is_primary']
        widgets = {
            'alt_text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        exclude = ['product', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control'}),
            'size': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'material': forms.TextInput(attrs={'class': 'form-control'}),
            'style': forms.TextInput(attrs={'class': 'form-control'}),
            'variant_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProductSpecificationForm(forms.ModelForm):
    class Meta:
        model = ProductSpecification
        exclude = ['product', 'created_at']
        widgets = {
            'specification_name': forms.TextInput(attrs={'class': 'form-control'}),
            'specification_value': forms.TextInput(attrs={'class': 'form-control'}),
        }

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'description', 'logo', 'website']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# Inline Formsets
ProductSpecificationFormSet = forms.inlineformset_factory(
    Product, ProductSpecification,
    form=ProductSpecificationForm,
    extra=1,
    can_delete=True
)

ProductImageFormSet = forms.inlineformset_factory(
    Product, ProductImage,
    form=ProductImageForm,
    extra=1,
    can_delete=True
)

ProductVariantFormSet = forms.inlineformset_factory(
    Product, ProductVariant,
    form=ProductVariantForm,
    extra=1,
    can_delete=True
)

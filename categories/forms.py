from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent', 'is_active', 'display_order', 'meta_title', 'meta_description', 'meta_keywords']

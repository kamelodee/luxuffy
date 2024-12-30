from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.urls import reverse
from ..forms import (
    ProductForm, ProductVariantFormSet, ProductImageFormSet,
    ProductSpecificationFormSet
)
from products.models import Product
from ..models import Vendor

@login_required
def product_list(request):
    vendor = get_object_or_404(Vendor, user=request.user)
    products = Product.objects.filter(vendor=vendor).order_by('-id')
    
    # Pagination
    paginator = Paginator(products, 10)  # Show 10 products per page
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    return render(request, 'vendors/products/product_list.html', {
        'products': products
    })

@login_required
@transaction.atomic
def product_create(request):
    vendor = get_object_or_404(Vendor, user=request.user)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, vendor=vendor)
        variant_formset = ProductVariantFormSet(request.POST, request.FILES, prefix='variants')
        image_formset = ProductImageFormSet(request.POST, request.FILES, prefix='images')
        spec_formset = ProductSpecificationFormSet(request.POST, prefix='specs')
        
        if (form.is_valid() and variant_formset.is_valid() and 
            image_formset.is_valid() and spec_formset.is_valid()):
            
            # Save the product
            product = form.save()
            
            # Save variants
            variant_formset.instance = product
            variant_formset.save()
            
            # Save images
            image_formset.instance = product
            image_formset.save()
            
            # Save specifications
            spec_formset.instance = product
            spec_formset.save()
            
            messages.success(request, 'Product created successfully!')
            return redirect('vendor_product_list')
    else:
        form = ProductForm(vendor=vendor)
        variant_formset = ProductVariantFormSet(prefix='variants')
        image_formset = ProductImageFormSet(prefix='images')
        spec_formset = ProductSpecificationFormSet(prefix='specs')
    
    return render(request, 'vendors/products/product_form.html', {
        'form': form,
        'variant_formset': variant_formset,
        'image_formset': image_formset,
        'spec_formset': spec_formset,
        'title': 'Create Product'
    })

@login_required
@transaction.atomic
def product_update(request, pk):
    vendor = get_object_or_404(Vendor, user=request.user)
    product = get_object_or_404(Product, pk=pk, vendor=vendor)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product, vendor=vendor)
        variant_formset = ProductVariantFormSet(request.POST, request.FILES, 
                                              instance=product, prefix='variants')
        image_formset = ProductImageFormSet(request.POST, request.FILES, 
                                          instance=product, prefix='images')
        spec_formset = ProductSpecificationFormSet(request.POST, 
                                                 instance=product, prefix='specs')
        
        if (form.is_valid() and variant_formset.is_valid() and 
            image_formset.is_valid() and spec_formset.is_valid()):
            
            # Save the product
            product = form.save()
            
            # Save variants
            variant_formset.save()
            
            # Save images
            image_formset.save()
            
            # Save specifications
            spec_formset.save()
            
            messages.success(request, 'Product updated successfully!')
            return redirect('vendor_product_list')
    else:
        form = ProductForm(instance=product, vendor=vendor)
        variant_formset = ProductVariantFormSet(instance=product, prefix='variants')
        image_formset = ProductImageFormSet(instance=product, prefix='images')
        spec_formset = ProductSpecificationFormSet(instance=product, prefix='specs')
    
    return render(request, 'vendors/products/product_form.html', {
        'form': form,
        'variant_formset': variant_formset,
        'image_formset': image_formset,
        'spec_formset': spec_formset,
        'product': product,
        'title': 'Update Product'
    })

@login_required
def product_delete(request, pk):
    vendor = get_object_or_404(Vendor, user=request.user)
    product = get_object_or_404(Product, pk=pk, vendor=vendor)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('vendor_product_list')
    
    return render(request, 'vendors/products/product_confirm_delete.html', {
        'product': product
    })

@login_required
def product_detail(request, pk):
    vendor = get_object_or_404(Vendor, user=request.user)
    product = get_object_or_404(Product, pk=pk, vendor=vendor)
    
    return render(request, 'vendors/products/product_detail.html', {
        'product': product
    })

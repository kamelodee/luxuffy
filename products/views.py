from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Product, ProductImage
from .forms import (
    ProductForm, ProductImageFormSet, ProductVariantFormSet, 
    ProductSpecificationFormSet
)
# Create your views here.

def detail(request):
    return render(request, 'product/detail.html')

def delete(request):
    return render(request, 'product/detail.html')

@login_required
def compare(request):
    """View for comparing products"""
    return render(request, 'product/compare.html')

@login_required
def wishlist(request):
    """View for user's wishlist"""
    return render(request, 'product/wishlist.html')

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        image_formset = ProductImageFormSet(request.POST, request.FILES, prefix='images')
        spec_formset = ProductSpecificationFormSet(request.POST, prefix='specs')
        variant_formset = ProductVariantFormSet(request.POST, request.FILES, prefix='variants')
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save the product
                    product = form.save(commit=False)
                    product.vendor = request.user.vendor  # Assuming user has a vendor profile
                    product.save()
                    form.save_m2m()  # Save many-to-many relationships
                    
                    # Handle formsets based on product type
                    if product.product_type == 'variable':
                        if variant_formset.is_valid():
                            variants = variant_formset.save(commit=False)
                            for variant in variants:
                                variant.product = product
                                variant.save()
                    
                    # Save images
                    if image_formset.is_valid():
                        images = image_formset.save(commit=False)
                        for image in images:
                            image.product = product
                            image.save()
                    
                    # Save specifications
                    if spec_formset.is_valid():
                        specs = spec_formset.save(commit=False)
                        for spec in specs:
                            spec.product = product
                            spec.save()
                    
                    messages.success(request, 'Product created successfully!')
                    return redirect('product_detail', slug=product.slug)
                    
            except Exception as e:
                messages.error(request, f'Error creating product: {str(e)}')
    else:
        form = ProductForm()
        image_formset = ProductImageFormSet(prefix='images')
        spec_formset = ProductSpecificationFormSet(prefix='specs')
        variant_formset = ProductVariantFormSet(prefix='variants')
    
    context = {
        'form': form,
        'image_formset': image_formset,
        'spec_formset': spec_formset,
        'variant_formset': variant_formset,
        'title': 'Create Product'
    }
    return render(request, 'products/product_form.html', context)

@login_required
def product_update(request, slug):
    product = get_object_or_404(Product, slug=slug, vendor=request.user.vendor)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        image_formset = ProductImageFormSet(request.POST, request.FILES, 
                                          instance=product, prefix='images')
        spec_formset = ProductSpecificationFormSet(request.POST, 
                                                 instance=product, prefix='specs')
        variant_formset = ProductVariantFormSet(request.POST, request.FILES, 
                                              instance=product, prefix='variants')
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    product = form.save()
                    
                    if product.product_type == 'variable':
                        if variant_formset.is_valid():
                            variant_formset.save()
                    
                    if image_formset.is_valid():
                        image_formset.save()
                    
                    if spec_formset.is_valid():
                        spec_formset.save()
                    
                    messages.success(request, 'Product updated successfully!')
                    return redirect('product_detail', slug=product.slug)
                    
            except Exception as e:
                messages.error(request, f'Error updating product: {str(e)}')
    else:
        form = ProductForm(instance=product)
        image_formset = ProductImageFormSet(instance=product, prefix='images')
        spec_formset = ProductSpecificationFormSet(instance=product, prefix='specs')
        variant_formset = ProductVariantFormSet(instance=product, prefix='variants')
    
    context = {
        'form': form,
        'image_formset': image_formset,
        'spec_formset': spec_formset,
        'variant_formset': variant_formset,
        'product': product,
        'title': 'Update Product'
    }
    return render(request, 'products/product_form.html', context)


@csrf_exempt
@require_POST
def upload_product_image(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
        image = request.FILES['file']
        product_image = ProductImage.objects.create(product=product, image=image)
        return JsonResponse({'success': True, 'image_id': product_image.id})
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

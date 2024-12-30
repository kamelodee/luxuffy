from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, Http404
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.forms import inlineformset_factory
from django.views import View
from django.db import transaction
from .models import Vendor
from products.models import Product, ProductVariant, ProductImage, ProductSpecification, Category
from products.forms import ProductForm, ProductVariantForm, ProductImageForm, ProductSpecificationForm
from .forms import VendorForm
from django.db.models import Q
from django.utils.text import slugify

class VendorRequiredMixin:
    """Verify that the current user has an associated vendor."""
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'vendor'):
            messages.error(request, 'You need to create a vendor account first.')
            return redirect('vendor_create')
        return super().dispatch(request, *args, **kwargs)

@login_required
def dashboard(request):
    """Vendor dashboard view."""
    if not hasattr(request.user, 'vendor'):
        return redirect('vendor_create')
    
    context = {
        'vendor': request.user.vendor,
        'recent_products': Product.objects.filter(vendor=request.user.vendor).order_by('-created_at')[:5],
        'total_products': Product.objects.filter(vendor=request.user.vendor).count(),
    }
    return render(request, 'vendor/dashboard.html', context)

@login_required
def vendor_create(request):
    """Create a new vendor."""
    if hasattr(request.user, 'vendor'):
        messages.warning(request, 'You already have a vendor account.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.user = request.user
            vendor.save()
            messages.success(request, 'Vendor account created successfully!')
            return redirect('dashboard')
    else:
        form = VendorForm()
    
    return render(request, 'vendors/vendor_form.html', {'form': form})

@login_required
def vendor_store(request, store_name):
    """Public vendor store view."""
    try:
        vendor = Vendor.objects.get(store_name=store_name)
        products = Product.objects.filter(
            vendor=vendor, 
            status='published',
            is_session=False
        ).order_by('-created_at')
        
        context = {
            'vendor': vendor,
            'products': products,
        }
        return render(request, 'vendors/store.html', context)
    except Vendor.DoesNotExist:
        raise Http404("Store not found")

# List all vendors
def vendor_list(request):
    vendors = Vendor.objects.all()
    return render(request, 'vendor/vendor_list.html', {'vendors': vendors})

# View details of a specific vendor
def vendor_detail(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    return render(request, 'vendor/vendor_detail.html', {'vendor': vendor})

# Product Views
class ProductListView(LoginRequiredMixin, VendorRequiredMixin, ListView):
    model = Product
    template_name = 'vendors/products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset().filter(vendor=self.request.user.vendor, is_session=False)
        
        # Apply search filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(sku__icontains=search_query)
            )
        
        # Apply category filter
        category = self.request.GET.get('category', '')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Apply status filter
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(is_active=(status == 'active'))
        
        # Apply sorting
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'price_low':
            queryset = queryset.order_by('price')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        
        # If it's an HTMX request, return only the products container
        if self.request.headers.get('HX-Request'):
            self.template_name = 'vendors/products/partials/product_list.html'
        
        return context

class LoadVariantsView(LoginRequiredMixin, VendorRequiredMixin, View):
    def get(self, request):
        product_id = request.GET.get('product_id')
        variants = []
        
        if product_id:
            product = get_object_or_404(Product, id=product_id, vendor=request.user.vendor)
            variants = product.variants.all()
            
        context = {
            'variants': [{'form': ProductVariantForm(instance=variant), 'variant': variant} for variant in variants],
            'product': {'id': product_id} if product_id else None
        }
        
        return render(request, 'vendors/products/partials/variants_section.html', context)

class AddVariantView(LoginRequiredMixin, VendorRequiredMixin, View):
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, vendor=request.user.vendor)
        variant_form = ProductVariantForm()
        
        return render(request, 'vendors/products/partials/variant_form.html', {
            'variant_form': variant_form,
            'variant': None,
            'counter': request.GET.get('counter', 1)
        })

class DeleteVariantView(LoginRequiredMixin, VendorRequiredMixin, View):
    def delete(self, request, variant_id):
        variant = get_object_or_404(ProductVariant, id=variant_id, product__vendor=request.user.vendor)
        variant.delete()
        return HttpResponse()

class InitiateProductCreation(LoginRequiredMixin, VendorRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            # Get or create unknown category
            unknown_category, _ = Category.objects.get_or_create(name='Unknown')
            
            # Create a default product with a unique slug
            base_name = 'New Product'
            base_slug = slugify(base_name)
            
            # Generate a unique slug
            counter = 1
            slug = base_slug
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Create the product
            product = Product.objects.create(
                vendor=request.user.vendor,
                name=base_name,
                slug=slug,
                category=unknown_category,
                price=0,
                product_type='simple',
                status='draft',
                is_session=True  # Mark as session product
            )
            
            messages.info(request, 'Started product creation session.')
            return redirect('vendor_product_edit', slug=product.slug)

class ProductCreateView(LoginRequiredMixin, VendorRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'vendors/products/product_form.html'
    success_url = reverse_lazy('vendor_products')
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user.vendor, is_session=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['variant_formset'] = self.get_variant_formset()(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            context['variant_formset'] = self.get_variant_formset()(instance=self.object)
        context['is_session'] = True
        context['product'] = self.object
        return context

    def get_variant_formset(self):
        return inlineformset_factory(
            Product, ProductVariant,
            form=ProductVariantForm,
            extra=1,
            can_delete=True,
            fields=['name', 'sku', 'price', 'stock_quantity', 'weight', 
                   'dimensions', 'size', 'color', 'material']
        )

    def form_valid(self, form):
        context = self.get_context_data()
        variant_formset = context['variant_formset']
        
        if form.cleaned_data.get('product_type') == 'variable':
            if not variant_formset.is_valid():
                messages.error(self.request, 'Please check the variant forms for errors.')
                return self.form_invalid(form)
            if not variant_formset.total_form_count():
                messages.error(self.request, 'Variable products must have at least one variant.')
                return self.form_invalid(form)
        
        # Set the vendor
        form.instance.vendor = self.request.user.vendor
        
        # Generate a unique slug from the product name
        name = form.cleaned_data['name']
        base_slug = slugify(name)
        counter = 1
        slug = base_slug
        
        # Check if we're updating an existing product
        if self.object and self.object.slug == slug:
            pass
        else:
            # Ensure slug uniqueness
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            form.instance.slug = slug
        
        form.instance.is_session = False  # Product is no longer in session
        
        try:
            with transaction.atomic():
                self.object = form.save()
                
                if self.object.product_type == 'variable':
                    variant_formset.instance = self.object
                    variant_formset.save()
            
            messages.success(self.request, 'Product saved successfully.')
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            messages.error(self.request, f'Error saving product: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error saving product. Please check the form.')
        return self.render_to_response(self.get_context_data(form=form))

class ProductUpdateView(LoginRequiredMixin, VendorRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'vendors/products/product_form.html'
    success_url = reverse_lazy('vendor_products')
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user.vendor)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['variant_formset'] = self.get_variant_formset()(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            context['variant_formset'] = self.get_variant_formset()(instance=self.object)
        context['product'] = self.object
        return context

    def get_variant_formset(self):
        return inlineformset_factory(
            Product, ProductVariant,
            form=ProductVariantForm,
            extra=1,
            can_delete=True
        )

    def form_valid(self, form):
        context = self.get_context_data()
        variant_formset = context['variant_formset']
        
        if form.cleaned_data.get('product_type') == 'variable' and not variant_formset.is_valid():
            return self.form_invalid(form)
            
        # Only update slug if name has changed
        if form.cleaned_data['name'] != self.object.name:
            base_slug = slugify(form.cleaned_data['name'])
            counter = 1
            slug = base_slug
            
            # Keep current slug if it's the same as what we'd generate
            if self.object.slug != slug:
                # Ensure slug uniqueness
                while Product.objects.exclude(pk=self.object.pk).filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                form.instance.slug = slug
        
        with transaction.atomic():
            self.object = form.save()
            
            if self.object.product_type == 'variable':
                variant_formset.instance = self.object
                variant_formset.save()
        
        messages.success(self.request, 'Product updated successfully.')
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, 'Error saving product. Please check the form.')
        return self.render_to_response(self.get_context_data(form=form))

class CancelProductCreation(LoginRequiredMixin, VendorRequiredMixin, View):
    def post(self, request, slug, *args, **kwargs):
        product = get_object_or_404(Product, slug=slug, vendor=request.user.vendor, is_session=True)
        product.delete()
        messages.info(request, 'Product creation cancelled.')
        return redirect('vendor_products')

class ProductDetailView(LoginRequiredMixin, VendorRequiredMixin, DetailView):
    model = Product
    template_name = 'vendors/products/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return super().get_queryset().filter(vendor=self.request.user.vendor)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        # If it's an HTMX request, return only the modal content
        if request.headers.get('HX-Request'):
            self.template_name = 'vendors/products/partials/product_detail_modal.html'
        
        return response

class ProductDeleteView(LoginRequiredMixin, VendorRequiredMixin, DeleteView):
    model = Product
    template_name = 'vendors/products/product_confirm_delete.html'
    success_url = reverse_lazy('vendor_products')
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return super().get_queryset().filter(vendor=self.request.user.vendor)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # If it's an HTMX request, return 204 No Content
        if request.headers.get('HX-Request'):
            self.object.delete()
            return HttpResponse(status=204)
        
        # Otherwise, proceed with normal deletion
        self.object.delete()
        return HttpResponseRedirect(success_url)


# Product Image Views
class ProductImageUploadView(LoginRequiredMixin, VendorRequiredMixin, View):
    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug, vendor=request.user.vendor)
        image = request.FILES.get('image')
        
        if not image:
            return JsonResponse({'error': 'No image provided'}, status=400)
            
        try:
            product_image = ProductImage.objects.create(
                product=product,
                image=image,
                alt_text=image.name,
                is_primary=not product.images.exists()  # First image is primary
            )
            return JsonResponse({'success': True, 'image_id': product_image.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class ProductImagesView(LoginRequiredMixin, VendorRequiredMixin, TemplateView):
    template_name = 'vendors/products/partials/product_images.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=kwargs['slug'], vendor=self.request.user.vendor)
        context['product'] = product
        return context

class SetPrimaryImageView(LoginRequiredMixin, VendorRequiredMixin, View):
    def post(self, request, image_id):
        image = get_object_or_404(ProductImage, id=image_id, product__vendor=request.user.vendor)
        product = image.product
        
        # Remove primary status from all other images
        product.images.update(is_primary=False)
        
        # Set this image as primary
        image.is_primary = True
        image.save()
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

class DeleteProductImageView(LoginRequiredMixin, VendorRequiredMixin, View):
    def delete(self, request, image_id):
        image = get_object_or_404(ProductImage, id=image_id, product__vendor=request.user.vendor)
        was_primary = image.is_primary
        product = image.product
        
        # Delete the image
        image.delete()
        
        # If this was the primary image, set a new primary
        if was_primary:
            new_primary = product.images.first()
            if new_primary:
                new_primary.is_primary = True
                new_primary.save()
        
        return HttpResponse(status=204)

class ProductImageCreateView(LoginRequiredMixin, VendorRequiredMixin, CreateView):
    model = ProductImage
    form_class = ProductImageForm
    template_name = 'vendors/products/partials/image_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, slug=self.kwargs['product_slug'], vendor=self.request.user.vendor)
        return context

    def form_valid(self, form):
        form.instance.product = get_object_or_404(Product, slug=self.kwargs['product_slug'], vendor=self.request.user.vendor)
        self.object = form.save()
        return render(self.request, 'vendors/products/partials/product_images.html', {'product': self.object.product})

class ProductImageDeleteView(LoginRequiredMixin, VendorRequiredMixin, DeleteView):
    model = ProductImage
    
    def get_queryset(self):
        return super().get_queryset().filter(product__vendor=self.request.user.vendor)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(status=204)

# Product Variant Views
class ProductVariantCreateView(LoginRequiredMixin, VendorRequiredMixin, CreateView):
    model = ProductVariant
    form_class = ProductVariantForm
    template_name = 'vendors/products/partials/variant_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, slug=self.kwargs['product_slug'], vendor=self.request.user.vendor)
        return context

    def form_valid(self, form):
        form.instance.product = get_object_or_404(Product, slug=self.kwargs['product_slug'], vendor=self.request.user.vendor)
        self.object = form.save()
        return render(self.request, 'vendors/products/partials/product_variants.html', {'product': self.object.product})

class ProductVariantEditView(LoginRequiredMixin, VendorRequiredMixin, UpdateView):
    model = ProductVariant
    form_class = ProductVariantForm
    template_name = 'vendors/products/partials/variant_form.html'

    def get_queryset(self):
        return super().get_queryset().filter(product__vendor=self.request.user.vendor)

    def form_valid(self, form):
        self.object = form.save()
        return render(self.request, 'vendors/products/partials/product_variants.html', {'product': self.object.product})

class ProductVariantDeleteView(LoginRequiredMixin, VendorRequiredMixin, DeleteView):
    model = ProductVariant
    
    def get_queryset(self):
        return super().get_queryset().filter(product__vendor=self.request.user.vendor)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(status=204)

# Product Specification Views
class ProductSpecificationCreateView(LoginRequiredMixin, VendorRequiredMixin, CreateView):
    model = ProductSpecification
    form_class = ProductSpecificationForm
    template_name = 'vendors/products/partials/specification_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, slug=self.kwargs['product_slug'], vendor=self.request.user.vendor)
        return context

    def form_valid(self, form):
        form.instance.product = get_object_or_404(Product, slug=self.kwargs['product_slug'], vendor=self.request.user.vendor)
        self.object = form.save()
        return render(self.request, 'vendors/products/partials/product_specifications.html', {'product': self.object.product})

class ProductSpecificationEditView(LoginRequiredMixin, VendorRequiredMixin, UpdateView):
    model = ProductSpecification
    form_class = ProductSpecificationForm
    template_name = 'vendors/products/partials/specification_form.html'

    def get_queryset(self):
        return super().get_queryset().filter(product__vendor=self.request.user.vendor)

    def form_valid(self, form):
        self.object = form.save()
        return render(self.request, 'vendors/products/partials/product_specifications.html', {'product': self.object.product})

class ProductSpecificationDeleteView(LoginRequiredMixin, VendorRequiredMixin, DeleteView):
    model = ProductSpecification
    
    def get_queryset(self):
        return super().get_queryset().filter(product__vendor=self.request.user.vendor)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(status=204)


@login_required
def setting(request):
    vendor = request.user.vendor  # Assuming there's a one-to-one relationship between User and Vendor
    if request.method == "POST":
        # Determine which form was submitted based on the fields present in POST data
        if 'business_name' in request.POST:
            # Store Information Update
            try:
                vendor.business_name = request.POST.get('business_name')
                vendor.business_type = request.POST.get('business_type')
                vendor.phone_number = request.POST.get('phone_number')
                vendor.phone_number2 = request.POST.get('phone_number2')
                vendor.store_name = request.POST.get('store_name')
                vendor.email = request.POST.get('email')

                # Handle file uploads if present
                if 'logo' in request.FILES:
                    vendor.logo = request.FILES['logo']
                if 'banner' in request.FILES:
                    vendor.banner = request.FILES['banner']

                vendor.save()
                messages.success(request, 'Store information updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating store information: {str(e)}')

        elif 'full_name' in request.POST:
            # Business Information Update
            try:
                vendor.full_name = request.POST.get('full_name')
                vendor.id_type = request.POST.get('id_type')
                vendor.id_number = request.POST.get('id_number')
                vendor.locality = request.POST.get('locality')
                vendor.region = request.POST.get('region')
                vendor.tin_number = request.POST.get('tin_number')
                vendor.address_line1 = request.POST.get('address_line1')
                vendor.address_line2 = request.POST.get('address_line2')
                vendor.city = request.POST.get('city')
                vendor.country = request.POST.get('country')

                # Handle ID document uploads
                if 'id_front' in request.FILES:
                    vendor.id_front = request.FILES['id_front']
                if 'id_back' in request.FILES:
                    vendor.id_back = request.FILES['id_back']

                vendor.save()
                messages.success(request, 'Business information updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating business information: {str(e)}')

        elif 'ship_from_address1' in request.POST:
            # Shipping Information Update
            try:
                # Shipping address
                vendor.ship_from_address1 = request.POST.get('ship_from_address1')
                vendor.ship_from_address2 = request.POST.get('ship_from_address2')
                vendor.ship_from_city = request.POST.get('ship_from_city')
                vendor.ship_from_region = request.POST.get('ship_from_region')
                vendor.ship_from_country = request.POST.get('ship_from_country')

                # Return address
                vendor.return_address1 = request.POST.get('return_address1')
                vendor.return_address2 = request.POST.get('return_address2')
                vendor.return_city = request.POST.get('return_city')
                vendor.return_region = request.POST.get('return_region')
                vendor.return_country = request.POST.get('return_country')

                vendor.save()
                messages.success(request, 'Shipping information updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating shipping information: {str(e)}')

        elif 'payment_type' in request.POST:
            # Payment Information Update
            try:
                vendor.payment_type = request.POST.get('payment_type')
                vendor.account_number = request.POST.get('account_number')
                vendor.mobile_money_number = request.POST.get('mobile_money_number')

                vendor.save()
                messages.success(request, 'Payment information updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating payment information: {str(e)}')

        return redirect('setting')
    vendor = Vendor.objects.filter(user=request.user).get()
    return render(request, 'vendor/setting.html', {'vendor': vendor})

# Create a new vendor
@login_required
def vendor_create(request):
    if hasattr(request.user, 'vendor'):
        messages.warning(request, 'You already have a vendor profile.')
        return redirect('vendor_products')

    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.user = request.user
            vendor.save()
            messages.success(request, 'Your vendor profile has been created successfully!')
            return redirect('vendor_products')
    else:
        form = VendorForm()
    
    return render(request, 'vendors/vendor_form.html', {'form': form})

# Update an existing vendor
def vendor_update(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            form.save()
            return redirect('vendor_list')
    else:
        form = VendorForm(instance=vendor)
    return render(request, 'vendor/vendor_form.html', {'form': form})

# Delete a vendor
def vendor_delete(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        vendor.delete()
        return redirect('vendor_list')
    return render(request, 'vendor/vendor_confirm_delete.html', {'vendor': vendor})

@login_required
def vendor_settings(request):
    """Handle vendor settings."""
    if not hasattr(request.user, 'vendor'):
        return redirect('vendor_create')
    
    vendor = request.user.vendor
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('vendor_settings')
    else:
        form = VendorForm(instance=vendor)
    
    return render(request, 'vendors/settings.html', {
        'form': form,
        'vendor': vendor
    })

class ToggleVariantSectionView(LoginRequiredMixin, VendorRequiredMixin, View):
    def get(self, request):
        product_type = request.GET.get('product_type')
        show_variants = product_type == 'variable'
        
        variant_formset = inlineformset_factory(
            Product, ProductVariant,
            form=ProductVariantForm,
            extra=1,
            can_delete=True,
            fields=['name', 'sku', 'price', 'stock_quantity', 'weight', 
                   'dimensions', 'size', 'color', 'material']
        )
        
        context = {
            'show_variants': show_variants,
            'variant_formset': variant_formset() if show_variants else None
        }
        
        return render(request, 'vendors/products/partials/variant_section.html', context)

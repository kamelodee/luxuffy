from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from .models import Category
from .forms import CategoryForm
from django.views.decorators.http import require_http_methods

# List View
def category_list(request):
    categories = Category.objects.all().order_by('display_order', 'name')
    return render(request, 'categories/category_list.html', {'categories': categories})

# Detail View
def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    return render(request, 'categories/category_detail.html', {'category': category})

# Create View
@require_http_methods(["GET", "POST"])
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'categories/category_form.html', {'form': form})

# Update View
@require_http_methods(["GET", "POST"])
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'categories/category_form.html', {'form': form})

# Delete View
@require_http_methods(["POST"])
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    return render(request, 'categories/category_confirm_delete.html', {'category': category})

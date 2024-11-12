from django.shortcuts import render

# Create your views here.

def detail(request):
    return render(request, 'product/detail.html')

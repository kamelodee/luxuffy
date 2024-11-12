
from django.shortcuts import render

# Create your views here.

def home(request):
    return render(request, 'home/index.html')

def about(request):
    return render(request, 'home/about-us.html')

def contact(request):
    return render(request, 'home/contact-us.html')


def faq(request):
    return render(request, 'home/faq.html')

def error(request):
    return render(request, 'home/error-404.html')

def stores(request):
    return render(request, 'home/store-list.html')

def shop(request):
    return render(request, 'home/shop.html')


def store(request):
    return render(request, 'home/store.html')


def compare(request):
    return render(request, 'home/compare.html')

def coming_soon(request):
    return render(request, 'home/comming-soon.html')


def become_vendor(request):
    return render(request, 'home/become-a-vendor.html')



def blog(request):
    return render(request, 'home/blog.html')

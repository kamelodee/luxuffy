from django.shortcuts import render

# Create your views here.
def wishlist(request):
    return render(request, 'account/wishlist.html')


def cart(request):
    return render(request, 'account/cart.html')

def checkout(request):
    return render(request, 'account/checkout.html')

def order(request):
    return render(request, 'account/order.html')

def my_acount(request):
    return render(request, 'account/my-account.html')

def login(request):
    return render(request, 'account/login.html')



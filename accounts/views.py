import ssl
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import uuid
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from datetime import timedelta
from .forms import *
from .models import User, Address, Order, OrderItem, WishlistItem, Notification, NotificationSettings
from .serializers import UserProfileSerializer, AddressSerializer, OrderSerializer, OrderDetailSerializer, WishlistItemSerializer, NotificationSerializer, NotificationSettingsSerializer
from django.contrib.auth import login as auth_login,logout
from django.contrib.auth import logout

from django.contrib.auth.forms import AuthenticationForm
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.conf import settings
from rest_framework.authtoken.models import Token
from google.oauth2 import id_token
from google.auth.transport import requests
from allauth.socialaccount.models import SocialAccount
from django.core.paginator import Paginator, EmptyPage, InvalidPage

def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)  # Use Django's `login` function renamed as `auth_login`
            
            # Handle "Remember Me"
            if not request.POST.get('remember_me'):
                request.session.set_expiry(0)  # Session expires when browser is closed
            else:
                request.session.set_expiry(1209600)  # 2 weeks

            return redirect('home')  # Redirect to a success page
    else:
        form = CustomAuthenticationForm()

    return render(request, 'account/login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email_verified = False
            user.verification_token = str(uuid.uuid4())
            user.save()
            
            # Send verification email
            verification_link = f"{settings.SITE_URL}/verify-email/{user.verification_token}"
            send_mail(
                'Verify your email',
                f'Click here to verify your email: {verification_link}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return render(request, 'authentication/registration_success.html')
    else:
        form = UserCreationForm()
    return render(request, 'account/signup.html', {"form":form})

def user_logout(request):
    logout(request)
    return redirect('home')

def request_password_reset(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                user.password_reset_token = str(uuid.uuid4())
                user.password_reset_expires = timezone.now() + timedelta(hours=24)
                user.save()
                
                # Send password reset email
                reset_link = f"{settings.SITE_URL}/reset-password/{user.password_reset_token}"
                send_mail(
                    'Password Reset Request',
                    f'Click here to reset your password: {reset_link}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                return render(request, 'account/password_reset_sent.html')
            except User.DoesNotExist:
                pass
    else:
        form = PasswordResetRequestForm()
    return render(request, 'account/request_password_reset.html', {'form': form})

def verify_email(request, token):
    User = get_user_model()
    user = get_object_or_404(User, verification_token=token)
    
    if not user.email_verified:
        user.email_verified = True
        user.verification_token = ''
        user.save()
        
        return render(request, 'account/email_verified.html')
    
    return redirect('login')

def reset_password(request, token):
    User = get_user_model()
    user = get_object_or_404(User, password_reset_token=token)
    
    if not user.password_reset_expires or user.password_reset_expires < timezone.now():
        return render(request, 'account/password_reset_expired.html')
    
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['password1'] == form.cleaned_data['password2']:
                user.set_password(form.cleaned_data['password1'])
                user.password_reset_token = ''
                user.password_reset_expires = None
                user.save()
                
                # Send password change confirmation email
                send_mail(
                    'Password Changed Successfully',
                    'Your password has been successfully changed.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                
                return render(request, 'account/password_reset_success.html')
    else:
        form = PasswordResetForm()
    
    return render(request, 'account/reset_password.html', {'form': form})

# API Views
from django.conf import settings
from google.oauth2.credentials import Credentials
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def google_login_api(request):
    """
    Endpoint for Google OAuth login
    Accepts either an ID token or authorization code
    """
    try:
        # Check for ID token (from web frontend)
        id_token = request.data.get('id_token')
        code = request.data.get('code')

        if not id_token and not code:
            return Response({
                'error': 'No token or authorization code provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        if id_token:
            try:
                # Verify the token with Google
                idinfo = google_id_token.verify_oauth2_token(
                    id_token,
                    google_requests.Request(),
                    settings.GOOGLE_OAUTH2_CLIENT_ID
                )

                if idinfo['aud'] != settings.GOOGLE_OAUTH2_CLIENT_ID:
                    raise ValueError('Wrong audience.')

                # Extract user info from ID token
                user_data = {
                    'email': idinfo['email'],
                    'given_name': idinfo.get('given_name', ''),
                    'family_name': idinfo.get('family_name', ''),
                    'id': idinfo['sub'],
                    'picture': idinfo.get('picture', '')
                }
            except ValueError:
                return Response({
                    'error': 'Invalid ID token'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Handle authorization code flow
            try:
                adapter = GoogleOAuth2Adapter()
                provider = adapter.get_provider()
                app = provider.get_app(request)
                client = OAuth2Client(
                    client_id=app.client_id,
                    client_secret=app.secret,
                    token_url=adapter.access_token_url,
                    redirect_uri=request.data.get('redirect_uri', settings.OAUTH2_REDIRECT_URIS[0])
                )
                
                # Exchange code for token
                token = client.get_access_token(code)
                access_token = token['access_token']
                
                # Get user info using access token
                user_data = provider.get_user_info(access_token)
            except Exception as e:
                return Response({
                    'error': f'Failed to authenticate with Google: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Process user data and create/update user
        email = user_data.get('email')
        if not email:
            return Response({
                'error': 'Email not provided by Google'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get or create user
        try:
            user = User.objects.get(email=email)
            created = False
        except User.DoesNotExist:
            # Create new user
            username = f"google_{user_data.get('id', '')}"
            user = User.objects.create_user(
                username=username,
                email=email,
                password=None,  # No password for social auth users
                first_name=user_data.get('given_name', ''),
                last_name=user_data.get('family_name', '')
            )
            created = True

            # Update profile
            if hasattr(user, 'profile'):
                profile = user.profile
                if user_data.get('picture'):
                    profile.avatar_url = user_data['picture']
                profile.email_verified = True
                profile.save()

        # Create or update social account
        social_account, _ = SocialAccount.objects.get_or_create(
            user=user,
            provider='google',
            defaults={'uid': user_data.get('id'), 'extra_data': user_data}
        )
        if not _:  # If social account already existed
            social_account.extra_data = user_data
            social_account.save()

        # Create or get auth token
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'token_type': 'Bearer',
            'access_token': token.key,
            'user_id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_new_user': created,
            'avatar_url': user.profile.avatar_url if hasattr(user, 'profile') else None
        })

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    API endpoint for email/password login
    Returns a Bearer token for authentication
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'error': 'Please provide both email and password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(email=email, password=password)
    
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token_type': 'Bearer',
            'access_token': token.key,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        })
    else:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """
    API endpoint for user registration
    """
    email = request.data.get('email')
    password = request.data.get('password')
    username = request.data.get('username')
    
    if not email or not password or not username:
        return Response({
            'error': 'Please provide email, password, and username'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=email).exists():
        return Response({
            'error': 'User with this email already exists'
        }, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({
            'error': 'Username is already taken'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.create_user(
            username=username,
            email=email, 
            password=password,
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', '')
        )
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'token_type': 'Bearer',
            'access_token': token.key,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_request_password_reset(request):
    form = PasswordResetRequestForm(request.data)
    if form.is_valid():
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            user.password_reset_token = str(uuid.uuid4())
            user.password_reset_expires = timezone.now() + timedelta(hours=24)
            user.save()
            
            # Send password reset email
            reset_link = f"{settings.SITE_URL}/reset-password/{user.password_reset_token}"
            send_mail(
                'Password Reset Request',
                f'Click here to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return Response({'message': 'Password reset email sent'})
        except User.DoesNotExist:
            pass
    return Response({'error': 'Invalid email'}, status=status.HTTP_400_BAD_REQUEST)

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

from django.core.mail import send_mail
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
def send_maila(request):
    sender_email = "noreply@luxuffy.com"
    receiver_email = "kamelodee@gmail.com"
    password = "System@19931993"  # Use environment variables for security
    
    # Create a secure SSL context
    context = ssl.create_default_context()
    context.check_hostname = False  # Disable hostname verification (for local/dev testing)
    context.verify_mode = ssl.CERT_NONE  # Skip cert verification (use carefully!)

    # Set up the MIMEText message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Test Email Subject"
    
    body = "This is a test email body."
    message.attach(MIMEText(body, "plain"))

    try:
        # Connect to the SMTP server using SSL
        with smtplib.SMTP_SSL("smtp.luxuffy.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            return 'success'
            print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from rest_framework.parsers import MultiPartParser, FormParser



@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def notifications_api(request):
    if request.method == 'GET':
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        
        # Apply filters
        notification_type = request.query_params.get('type')
        if notification_type:
            notifications = notifications.filter(type=notification_type)
        
        read_status = request.query_params.get('read')
        if read_status is not None:
            notifications = notifications.filter(read=read_status.lower() == 'true')
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        paginator = Paginator(notifications, page_size)
        
        try:
            notifications = paginator.page(page)
        except (EmptyPage, InvalidPage):
            return Response([], status=status.HTTP_200_OK)
        
        serializer = NotificationSerializer(notifications, many=True)
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page
        })
    
    if request.method == 'POST':
        notification_id = request.data.get('notification_id')
        if not notification_id:
            return Response({'error': 'notification_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.read = True
            notification.save()
            return Response({'status': 'success'})
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def notification_settings_api(request):
    settings = NotificationSettings.objects.get_or_create(user=request.user)[0]
    
    if request.method == 'GET':
        serializer = NotificationSettingsSerializer(settings)
        return Response(serializer.data)
    
    if request.method == 'PUT':
        serializer = NotificationSettingsSerializer(settings, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def wishlist_api(request):
    if request.method == 'GET':
        wishlist_items = WishlistItem.objects.filter(user=request.user)
        
        # Apply filters
        in_stock = request.query_params.get('in_stock')
        if in_stock is not None:
            wishlist_items = wishlist_items.filter(in_stock=in_stock.lower() == 'true')
        
        min_price = request.query_params.get('min_price')
        if min_price:
            wishlist_items = wishlist_items.filter(price__gte=min_price)
        
        max_price = request.query_params.get('max_price')
        if max_price:
            wishlist_items = wishlist_items.filter(price__lte=max_price)
        
        # Sort
        sort_by = request.query_params.get('sort', '-added_date')
        if sort_by in ['added_date', '-added_date', 'price', '-price', 'name', '-name']:
            wishlist_items = wishlist_items.order_by(sort_by)
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 12))
        paginator = Paginator(wishlist_items, page_size)
        
        try:
            wishlist_items = paginator.page(page)
        except (EmptyPage, InvalidPage):
            return Response([], status=status.HTTP_200_OK)
        
        serializer = WishlistItemSerializer(wishlist_items, many=True)
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page
        })
    
    if request.method == 'POST':
        serializer = WishlistItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def wishlist_item_api(request, product_id):
    try:
        item = WishlistItem.objects.get(user=request.user, product_id=product_id)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except WishlistItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

@login_required
def order_history(request):
    return render(request, 'account/order_history.html')

@login_required
def address_book(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'account/address_book.html', {'addresses': addresses})

@login_required
def notifications(request):
    return render(request, 'account/notifications.html')

# API Views for Profile Management
# @api_view(['GET', 'POST'])
# @permission_classes([permissions.IsAuthenticated])
# def profile_settings_api(request):
#     if request.method == 'GET':
#         serializer = UserProfileSerializer(request.user)
#         return Response(serializer.data)
#     elif request.method == 'POST':
#         serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password_api(request):
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        if user.check_password(serializer.data.get('current_password')):
            user.set_password(serializer.data.get('new_password'))
            user.save()
            return Response({'message': 'Password changed successfully'})
        return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def manage_addresses_api(request):
    """
    Get addresses with filtering
    Query params:
    - is_default: Filter default addresses (true/false)
    - country: Filter by country
    - sort: Sort by (created_at, -created_at)
    """
    is_default = request.GET.get('is_default')
    country = request.GET.get('country')
    sort = request.GET.get('sort', '-created_at')

    addresses = Address.objects.filter(user=request.user)

    if is_default is not None:
        is_default = is_default.lower() == 'true'
        addresses = addresses.filter(is_default=is_default)
    if country:
        addresses = addresses.filter(country=country)

    addresses = addresses.order_by(sort)
    serializer = AddressSerializer(addresses, many=True)
    
    return Response({
        'results': serializer.data,
        'count': addresses.count()
    })

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def manage_addresses(request, address_id=None):
    """
    Manage user addresses
    """
    user = request.user

    if request.method == 'GET':
        if address_id:
            try:
                address = Address.objects.get(id=address_id, user=user)
                data = {
                    'id': address.id,
                    'address_line_1': address.address_line_1,
                    'address_line_2': address.address_line_2,
                    'city': address.city,
                    'state': address.state,
                    'postal_code': address.postal_code,
                    'country': address.country,
                    'is_primary': address.is_primary
                }
                return Response(data)
            except Address.DoesNotExist:
                return Response({
                    'error': 'Address not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            addresses = Address.objects.filter(user=user)
            data = [{
                'id': addr.id,
                'address_line_1': addr.address_line_1,
                'address_line_2': addr.address_line_2,
                'city': addr.city,
                'state': addr.state,
                'postal_code': addr.postal_code,
                'country': addr.country,
                'is_primary': addr.is_primary
            } for addr in addresses]
            return Response(data)

    elif request.method == 'POST':
        # Create new address
        try:
            address = Address.objects.create(
                user=user,
                address_line_1=request.data.get('address_line_1'),
                address_line_2=request.data.get('address_line_2', ''),
                city=request.data.get('city'),
                state=request.data.get('state'),
                postal_code=request.data.get('postal_code'),
                country=request.data.get('country'),
                is_primary=request.data.get('is_primary', False)
            )
            
            # If this is primary, unset other primary addresses
            if address.is_primary:
                Address.objects.filter(user=user).exclude(id=address.id).update(is_primary=False)

            return Response({
                'message': 'Address added successfully',
                'address_id': address.id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        if not address_id:
            return Response({
                'error': 'Address ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            address = Address.objects.get(id=address_id, user=user)
            
            # Update address fields
            if 'address_line_1' in request.data:
                address.address_line_1 = request.data['address_line_1']
            if 'address_line_2' in request.data:
                address.address_line_2 = request.data['address_line_2']
            if 'city' in request.data:
                address.city = request.data['city']
            if 'state' in request.data:
                address.state = request.data['state']
            if 'postal_code' in request.data:
                address.postal_code = request.data['postal_code']
            if 'country' in request.data:
                address.country = request.data['country']
            if 'is_primary' in request.data:
                address.is_primary = request.data['is_primary']
                if address.is_primary:
                    Address.objects.filter(user=user).exclude(id=address.id).update(is_primary=False)

            address.save()
            return Response({
                'message': 'Address updated successfully'
            })
        except Address.DoesNotExist:
            return Response({
                'error': 'Address not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if not address_id:
            return Response({
                'error': 'Address ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            address = Address.objects.get(id=address_id, user=user)
            address.delete()
            return Response({
                'message': 'Address deleted successfully'
            })
        except Address.DoesNotExist:
            return Response({
                'error': 'Address not found'
            }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def order_history_api(request):
    """
    Get order history with filtering and pagination
    Query params:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10)
    - status: Order status filter (pending, processing, shipped, delivered, cancelled)
    - start_date: Filter orders from this date (YYYY-MM-DD)
    - end_date: Filter orders until this date (YYYY-MM-DD)
    - sort: Sort orders by (date, -date, total_amount, -total_amount)
    """
    # Get query parameters
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    sort = request.GET.get('sort', '-date')

    # Base queryset
    orders = Order.objects.filter(user=request.user)

    # Apply filters
    if status:
        orders = orders.filter(status=status)
    if start_date:
        orders = orders.filter(date__gte=start_date)
    if end_date:
        orders = orders.filter(date__lte=end_date)

    # Apply sorting
    if sort:
        orders = orders.order_by(sort)

    # Pagination
    paginator = Paginator(orders, page_size)
    try:
        orders_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        orders_page = paginator.page(paginator.num_pages)

    serializer = OrderSerializer(orders_page, many=True)
    
    return Response({
        'results': serializer.data,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'has_next': orders_page.has_next(),
        'has_previous': orders_page.has_previous()
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notifications_api(request):
    """
    Get notifications with filtering and pagination
    Query params:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20)
    - read: Filter by read status (true/false)
    - type: Notification type (order_update, promotion, system)
    - sort: Sort by (created_at, -created_at)
    """
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    read = request.GET.get('read')
    notification_type = request.GET.get('type')
    sort = request.GET.get('sort', '-created_at')

    notifications = Notification.objects.filter(user=request.user)

    if read is not None:
        read = read.lower() == 'true'
        notifications = notifications.filter(read=read)
    if notification_type:
        notifications = notifications.filter(type=notification_type)

    notifications = notifications.order_by(sort)

    paginator = Paginator(notifications, page_size)
    try:
        notifications_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        notifications_page = paginator.page(paginator.num_pages)

    serializer = NotificationSerializer(notifications_page, many=True)
    
    return Response({
        'results': serializer.data,
        'unread_count': notifications.filter(read=False).count(),
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'has_next': notifications_page.has_next(),
        'has_previous': notifications_page.has_previous()
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def wishlist_api(request):
    """
    Get wishlist items with filtering and pagination
    Query params:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 12)
    - in_stock: Filter by stock status (true/false)
    - min_price: Minimum price filter
    - max_price: Maximum price filter
    - sort: Sort by (added_date, -added_date, price, -price, name, -name)
    """
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 12))
    in_stock = request.GET.get('in_stock')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort', '-added_date')

    wishlist_items = WishlistItem.objects.filter(user=request.user)

    if in_stock is not None:
        in_stock = in_stock.lower() == 'true'
        wishlist_items = wishlist_items.filter(in_stock=in_stock)
    if min_price:
        wishlist_items = wishlist_items.filter(price__gte=float(min_price))
    if max_price:
        wishlist_items = wishlist_items.filter(price__lte=float(max_price))

    wishlist_items = wishlist_items.order_by(sort)

    paginator = Paginator(wishlist_items, page_size)
    try:
        items_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        items_page = paginator.page(paginator.num_pages)

    serializer = WishlistItemSerializer(items_page, many=True)
    
    return Response({
        'results': serializer.data,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'has_next': items_page.has_next(),
        'has_previous': items_page.has_previous()
    })

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def manage_addresses_api(request):
    """
    Get addresses with filtering
    Query params:
    - is_default: Filter default addresses (true/false)
    - country: Filter by country
    - sort: Sort by (created_at, -created_at)
    """
    is_default = request.GET.get('is_default')
    country = request.GET.get('country')
    sort = request.GET.get('sort', '-created_at')

    addresses = Address.objects.filter(user=request.user)

    if is_default is not None:
        is_default = is_default.lower() == 'true'
        addresses = addresses.filter(is_default=is_default)
    if country:
        addresses = addresses.filter(country=country)

    addresses = addresses.order_by(sort)
    serializer = AddressSerializer(addresses, many=True)
    
    return Response({
        'results': serializer.data,
        'count': addresses.count()
    })

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def manage_address_api(request, address_id):
    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AddressSerializer(address)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = AddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'PUT':
        serializer = AddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def order_history_api(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def order_detail_api(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    serializer = OrderDetailSerializer(order)
    return Response(serializer.data)

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def wishlist_api(request):
    if request.method == 'GET':
        wishlist_items = WishlistItem.objects.filter(user=request.user)
        serializer = WishlistItemSerializer(wishlist_items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = WishlistItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def wishlist_item_api(request, product_id):
    try:
        wishlist_item = WishlistItem.objects.get(user=request.user, product_id=product_id)
        wishlist_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except WishlistItem.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notifications_api(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    return Response({
        'notifications': serializer.data,
        'unread_count': notifications.filter(read=False).count()
    })

@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def notification_settings_api(request):
    settings, created = NotificationSettings.objects.get_or_create(user=request.user)
    if request.method == 'GET':
        serializer = NotificationSettingsSerializer(settings)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = NotificationSettingsSerializer(settings, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# OAuth Views
def google_login(request):
    # Handle Google OAuth login
    return redirect('google_callback')

def google_callback(request):
    # Handle Google OAuth callback
    return redirect('profile')

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile, Address, Order, WishlistItem, Notification, NotificationSettings
from .serializers import UserProfileSerializer, AddressSerializer, OrderSerializer, OrderDetailSerializer, WishlistItemSerializer, NotificationSerializer, NotificationSettingsSerializer

# Web Views
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')
        return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        # Handle registration logic
        return redirect('login')
    return render(request, 'accounts/register.html')

@login_required
def request_password_reset(request):
    if request.method == 'POST':
        # Handle password reset request
        return redirect('login')
    return render(request, 'accounts/password_reset.html')

def reset_password(request, token):
    if request.method == 'POST':
        # Handle password reset
        return redirect('login')
    return render(request, 'accounts/reset_password.html')

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def profile_settings_api(request):
    profile = request.user.profile
    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = UserProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_api(request):
    # Handle password change
    return Response(status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_addresses_api(request):
    if request.method == 'GET':
        addresses = Address.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_address_api(request, address_id):
    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AddressSerializer(address)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = AddressSerializer(address, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_history_api(request):
    orders = Order.objects.filter(user=request.user)
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail_api(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    serializer = OrderDetailSerializer(order)
    return Response(serializer.data)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def wishlist_api(request):
    if request.method == 'GET':
        wishlist = WishlistItem.objects.filter(user=request.user)
        serializer = WishlistItemSerializer(wishlist, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = WishlistItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def wishlist_item_api(request, product_id):
    try:
        item = WishlistItem.objects.get(user=request.user, product_id=product_id)
    except WishlistItem.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_api(request):
    notifications = Notification.objects.filter(user=request.user)
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def notification_settings_api(request):
    settings, created = NotificationSettings.objects.get_or_create(user=request.user)
    if request.method == 'GET':
        serializer = NotificationSettingsSerializer(settings)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = NotificationSettingsSerializer(settings, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# OAuth Views
def google_login(request):
    # Handle Google OAuth login
    return redirect('google_callback')

def google_callback(request):
    # Handle Google OAuth callback
    return redirect('profile')

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def api_logout(request):
    """
    Logout the user and invalidate their auth token
    """
    if hasattr(request.user, 'auth_token'):
        request.user.auth_token.delete()
    return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)

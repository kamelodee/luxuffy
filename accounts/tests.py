from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from .models import Address, Order, WishlistItem, Notification, NotificationSettings
import json
from django.utils import timezone

User = get_user_model()

class AccountsAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a test user
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=self.user)

        # Create test address
        self.address_data = {
            'label': 'home',
            'address_line1': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'postal_code': '12345',
            'country': 'Test Country'
        }
        self.address = Address.objects.create(user=self.user, **self.address_data)

    def test_user_registration(self):
        """Test user registration endpoint"""
        url = reverse('api_register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_user_login(self):
        """Test user login endpoint"""
        url = reverse('api_login')
        data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_user_profile(self):
        """Test user profile endpoints"""
        # Get profile
        url = reverse('api_profile_settings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_data['email'])

        # Update profile
        update_data = {
            'first_name': 'Updated',
            'phone_number': '1234567890'
        }
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['phone_number'], '1234567890')

    def test_address_operations(self):
        """Test address CRUD operations"""
        # Create address
        url = reverse('api_addresses')
        new_address_data = {
            'label': 'work',
            'address_line1': '456 Work St',
            'city': 'Work City',
            'state': 'Work State',
            'postal_code': '67890',
            'country': 'Work Country'
        }
        response = self.client.post(url, new_address_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get address list
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Including the address created in setUp

        # Update address
        address_id = response.data[0]['id']
        url = reverse('api_address_detail', args=[address_id])
        update_data = {'city': 'Updated City'}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['city'], 'Updated City')

        # Delete address
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_order_operations(self):
        """Test order operations"""
        url = reverse('api_orders')
        # Create order
        order_data = {
            'order_number': 'ORD123',
            'total_amount': '199.99',
            'shipping_address': self.address.id,
            'items': [
                {
                    'product_id': 'prod123',
                    'name': 'Test Product',
                    'quantity': 2,
                    'price': '99.99'
                }
            ]
        }
        response = self.client.post(url, order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get order list
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Get order detail
        order_id = response.data[0]['id']
        url = reverse('api_order_detail', args=[order_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)

    def test_wishlist_operations(self):
        """Test wishlist operations"""
        url = reverse('api_wishlist')
        # Add item to wishlist
        wishlist_data = {
            'product_id': 'test123',
            'name': 'Test Product',
            'price': '99.99'
        }
        response = self.client.post(url, wishlist_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get wishlist
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Remove from wishlist
        product_id = response.data[0]['product_id']
        url = reverse('api_wishlist_item', args=[product_id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_notification_operations(self):
        """Test notification operations"""
        # Get notifications
        url = reverse('api_notifications')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Mark notification as read
        notification = Notification.objects.create(
            user=self.user,
            type='system',
            title='Test Notification',
            message='Test Message'
        )
        url = reverse('api_notifications')
        response = self.client.post(url, {'notification_id': notification.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.read)

    def test_notification_settings(self):
        """Test notification settings operations"""
        url = reverse('api_notification_settings')
        # Get settings
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update settings
        settings_data = {
            'email_notifications': {
                'order_updates': True,
                'promotions': False
            },
            'push_notifications': {
                'order_updates': True,
                'promotions': True
            }
        }
        response = self.client.put(url, settings_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['email_notifications']['order_updates'],
            settings_data['email_notifications']['order_updates']
        )

    def test_password_reset(self):
        """Test password reset flow"""
        # Request password reset
        url = reverse('api_password_reset')
        data = {'email': self.user_data['email']}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Get user and verify token was set
        user = User.objects.get(email=self.user_data['email'])
        self.assertIsNotNone(user.password_reset_token)
        self.assertIsNotNone(user.password_reset_expires)

        # Reset password
        url = reverse('api_password_reset')
        data = {
            'token': user.password_reset_token,
            'new_password': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Try logging in with new password
        url = reverse('api_login')
        data = {
            'email': self.user_data['email'],
            'password': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_email_verification(self):
        """Test email verification flow"""
        # Request email verification
        url = reverse('api_email_verification')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Get user and verify token was set
        user = User.objects.get(email=self.user_data['email'])
        self.assertIsNotNone(user.verification_token)

        # Verify email
        url = reverse('api_email_verification')
        data = {'token': user.verification_token}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that email is verified
        user.refresh_from_db()
        self.assertTrue(user.email_verified)

    def test_user_registration_validation(self):
        """Test user registration validation"""
        url = reverse('api_register')
        
        # Test invalid email
        data = {
            'email': 'invalid-email',
            'username': 'testuser2',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

        # Test duplicate email
        data['email'] = self.user_data['email']
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

        # Test weak password
        data = {
            'email': 'new@example.com',
            'username': 'testuser2',
            'password': '123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_user_login_validation(self):
        """Test user login validation"""
        url = reverse('api_login')

        # Test invalid credentials
        data = {
            'email': self.user_data['email'],
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test non-existent user
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test inactive user
        self.user.is_active = False
        self.user.save()
        data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_update_validation(self):
        """Test profile update validation"""
        url = reverse('api_profile_settings')

        # Test invalid phone number format
        update_data = {
            'phone_number': 'invalid-phone'
        }
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)

        # Test invalid date format
        update_data = {
            'date_of_birth': 'invalid-date'
        }
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date_of_birth', response.data)

    def test_address_validation(self):
        """Test address validation"""
        url = reverse('api_addresses')

        # Test missing required fields
        data = {
            'label': 'home'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('address_line1', response.data)

        # Test invalid postal code
        data = {
            'label': 'home',
            'address_line1': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'postal_code': 'invalid',
            'country': 'Test Country'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('postal_code', response.data)

    def test_order_validation(self):
        """Test order validation"""
        url = reverse('api_orders')

        # Test empty order items
        order_data = {
            'order_number': 'ORD123',
            'total_amount': '199.99',
            'shipping_address': self.address.id,
            'items': []
        }
        response = self.client.post(url, order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('items', response.data)

        # Test invalid total amount
        order_data = {
            'order_number': 'ORD123',
            'total_amount': 'invalid',
            'shipping_address': self.address.id,
            'items': [
                {
                    'product_id': 'prod123',
                    'name': 'Test Product',
                    'quantity': 2,
                    'price': '99.99'
                }
            ]
        }
        response = self.client.post(url, order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('total_amount', response.data)

        # Test non-existent shipping address
        order_data = {
            'order_number': 'ORD123',
            'total_amount': '199.99',
            'shipping_address': 9999,
            'items': [
                {
                    'product_id': 'prod123',
                    'name': 'Test Product',
                    'quantity': 2,
                    'price': '99.99'
                }
            ]
        }
        response = self.client.post(url, order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('shipping_address', response.data)

    def test_wishlist_validation(self):
        """Test wishlist validation"""
        url = reverse('api_wishlist')

        # Test duplicate product
        wishlist_data = {
            'product_id': 'test123',
            'name': 'Test Product',
            'price': '99.99'
        }
        self.client.post(url, wishlist_data, format='json')
        response = self.client.post(url, wishlist_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product_id', response.data)

        # Test invalid price
        wishlist_data = {
            'product_id': 'test456',
            'name': 'Test Product',
            'price': 'invalid'
        }
        response = self.client.post(url, wishlist_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)

    def test_notification_settings_validation(self):
        """Test notification settings validation"""
        url = reverse('api_notification_settings')

        # Test invalid notification type
        settings_data = {
            'email_notifications': {
                'invalid_type': True
            }
        }
        response = self.client.put(url, settings_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email_notifications', response.data)

        # Test invalid value type
        settings_data = {
            'email_notifications': {
                'order_updates': 'invalid'
            }
        }
        response = self.client.put(url, settings_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email_notifications', response.data)

    def test_password_reset_validation(self):
        """Test password reset validation"""
        # Test invalid email
        url = reverse('api_password_reset')
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Test invalid token
        url = reverse('api_password_reset')
        data = {
            'token': 'invalid-token',
            'new_password': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', response.data)

        # Test expired token
        self.user.password_reset_token = 'valid-token'
        self.user.password_reset_expires = timezone.now() - timezone.timedelta(hours=25)
        self.user.save()
        data = {
            'token': 'valid-token',
            'new_password': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', response.data)

    def test_email_verification_validation(self):
        """Test email verification validation"""
        # Test invalid token
        url = reverse('api_email_verification')
        data = {'token': 'invalid-token'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', response.data)

        # Test already verified email
        self.user.email_verified = True
        self.user.save()
        url = reverse('api_email_verification')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        self.client.force_authenticate(user=None)
        
        # Test profile access
        url = reverse('api_profile_settings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test address access
        url = reverse('api_addresses')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test order access
        url = reverse('api_orders')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test wishlist access
        url = reverse('api_wishlist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test notification access
        url = reverse('api_notifications')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

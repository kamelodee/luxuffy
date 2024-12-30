from django.test import TestCase, Client, override_settings, TransactionTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from chat_to_shop.routing import websocket_urlpatterns
from chat_to_shop.consumers.chat import ChatConsumer
from chat_to_shop.consumers.video_shop import VideoShopConsumer
from chat_to_shop.models import Product, Order
from vendors.models import Vendor
from categories.models import Category
from decimal import Decimal
import json
import uuid
from channels.auth import AuthMiddlewareStack
from django.db import connection

@override_settings(
    SESSION_ENGINE='django.contrib.sessions.backends.file',
    CHANNEL_LAYERS={
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer"
        }
    }
)
class ChatToShopTests(TransactionTestCase):
    def setUp(self):
        """Set up test data"""
        # Create unique identifiers for this test run
        self.test_id = str(uuid.uuid4())[:8]
        self.client = Client()
        User = get_user_model()
        
        # Disable foreign key checks
        with connection.cursor() as cursor:
            cursor.execute('SET CONSTRAINTS ALL DEFERRED;')
        
        try:
            # Create regular user
            self.user = User.objects.create_user(
                username=f'testuser_{self.test_id}',
                email=f'test_{self.test_id}@example.com',
                password='testpass123'
            )
            
            # Create vendor user
            self.vendor_user = User.objects.create_user(
                username=f'vendor_{self.test_id}',
                email=f'vendor_{self.test_id}@example.com',
                password='vendor123'
            )
            
            # Create vendor profile
            self.vendor = Vendor.objects.create(
                user=self.vendor_user,
                business_name=f'Test Store {self.test_id}',
                business_type='individual'
            )
            
            # Create test category
            self.category = Category.objects.create(
                name=f'Test Category {self.test_id}',
                description='Test category description'
            )
            
            # Create test product
            self.product = Product.objects.create(
                vendor=self.vendor,
                name=f'Test Product {self.test_id}',
                description='Test product description',
                price=Decimal('99.99'),
                category=self.category
            )
            
            self.client.login(username=f'testuser_{self.test_id}', password='testpass123')
        finally:
            # Re-enable foreign key checks
            with connection.cursor() as cursor:
                cursor.execute('SET CONSTRAINTS ALL IMMEDIATE;')

    def tearDown(self):
        """Clean up after each test"""
        # Disable foreign key checks
        with connection.cursor() as cursor:
            cursor.execute('SET CONSTRAINTS ALL DEFERRED;')
            
        try:
            # Delete test data in reverse order to handle foreign key constraints
            Product.objects.filter(name__startswith='Test Product').delete()
            Category.objects.filter(name__startswith='Test Category').delete()
            Vendor.objects.filter(business_name__startswith='Test Store').delete()
            get_user_model().objects.filter(username__in=[
                f'testuser_{self.test_id}',
                f'vendor_{self.test_id}'
            ]).delete()
            
            # Clean up the test database
            cursor.execute("""
                DO $$ 
                BEGIN
                    -- Disable all triggers
                    EXECUTE (
                        SELECT string_agg('ALTER TABLE ' || quote_ident(schemaname) || '.' || quote_ident(tablename) || ' DISABLE TRIGGER ALL;', ' ')
                        FROM pg_tables
                        WHERE schemaname = 'public'
                    );
                    
                    -- Drop all tables
                    EXECUTE (
                        SELECT string_agg('DROP TABLE IF EXISTS ' || quote_ident(schemaname) || '.' || quote_ident(tablename) || ' CASCADE;', ' ')
                        FROM pg_tables
                        WHERE schemaname = 'public'
                    );
                END $$;
            """)
        finally:
            # Re-enable foreign key checks
            with connection.cursor() as cursor:
                cursor.execute('SET CONSTRAINTS ALL IMMEDIATE;')

    async def test_chat_room_connection(self):
        """Test chat room WebSocket connection"""
        application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        communicator = WebsocketCommunicator(
            application,
            "/ws/chat/room/testroom/",
            {"user": self.user}
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_chat_message_handling(self):
        """Test chat message sending and receiving"""
        application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        communicator = WebsocketCommunicator(
            application,
            "/ws/chat/room/testroom/",
            {"user": self.user}
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Test sending message
        await communicator.send_json_to({
            'type': 'chat_message',
            'message': 'Hello, world!'
        })

        # Test receiving response
        response = await communicator.receive_json_from()
        self.assertIn('message', response)
        self.assertIn('Hello, world!', response['message'])

        await communicator.disconnect()

    async def test_video_shop_connection(self):
        """Test video shop WebSocket connection"""
        application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        communicator = WebsocketCommunicator(
            application,
            "/ws/video_shop/",
            {"user": self.user}
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_product_interaction(self):
        """Test product interaction through WebSocket"""
        application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        communicator = WebsocketCommunicator(
            application,
            "/ws/video_shop/",
            {"user": self.user}
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Test product query
        await communicator.send_json_to({
            'type': 'product_query',
            'product_id': self.product.id
        })

        # Test receiving response
        response = await communicator.receive_json_from()
        self.assertIn('product', response)
        self.assertEqual(response['product']['name'], f'Test Product {self.test_id}')

        await communicator.disconnect()

    def test_chat_room_view(self):
        """Test chat room view"""
        response = self.client.get(reverse('chat_to_shop:chat_room', args=['testroom']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat_to_shop/chat_room.html')

    def test_video_shop_view(self):
        """Test video shop view"""
        response = self.client.get(reverse('chat_to_shop:video_shop'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_shop/video_feed.html')

    def test_vendor_dashboard_view(self):
        """Test vendor dashboard view"""
        # Test access denied for non-vendor
        response = self.client.get(reverse('chat_to_shop:vendor_dashboard'))
        self.assertEqual(response.status_code, 403)
        
        # Login as vendor user
        self.client.login(username=f'vendor_{self.test_id}', password='vendor123')
        
        # Test access granted for vendor
        response = self.client.get(reverse('chat_to_shop:vendor_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat_to_shop/vendor_dashboard.html')

    def test_unauthenticated_access(self):
        """Test access control for unauthenticated users"""
        self.client.logout()
        
        # Test video shop access
        response = self.client.get(reverse('chat_to_shop:video_shop'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test chat room access
        response = self.client.get(reverse('chat_to_shop:chat_room', args=['testroom']))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    async def test_chat_consumer_authentication(self):
        application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        
        # Test unauthenticated connection
        communicator = WebsocketCommunicator(
            application=application,
            path='/ws/chat/testroom/'
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Send a message as unauthenticated user
        await communicator.send_json_to({
            'message': 'Hello World'
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['user'], 'Anonymous')
        
        await communicator.disconnect()
        
        # Test authenticated connection
        scope = {'user': self.user}
        communicator = WebsocketCommunicator(
            application=application,
            path='/ws/chat/testroom/',
            headers=[(b'user', str(self.user.id).encode())]
        )
        communicator.scope['user'] = self.user
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Send a message as authenticated user
        await communicator.send_json_to({
            'message': 'Hello World'
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['user'], self.user.username)
        
        await communicator.disconnect()

    async def test_video_shop_consumer_authentication(self):
        application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        
        # Test unauthenticated connection
        communicator = WebsocketCommunicator(
            application=application,
            path='/ws/video_shop/'
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Try to perform authenticated action
        await communicator.send_json_to({
            'type': 'get_product_details',
            'product_id': self.product.id
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'error')
        self.assertEqual(response['message'], 'Authentication required')
        
        await communicator.disconnect()
        
        # Test authenticated connection
        scope = {'user': self.user}
        communicator = WebsocketCommunicator(
            application=application,
            path='/ws/video_shop/',
            headers=[(b'user', str(self.user.id).encode())]
        )
        communicator.scope['user'] = self.user
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Get initial content
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'initial_content')
        self.assertEqual(response['user'], self.user.username)
        
        await communicator.disconnect()

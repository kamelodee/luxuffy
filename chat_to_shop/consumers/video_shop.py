import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from ..models import VideoContent, LiveStream
from products.models import Product
from orders.models import Order
from datetime import datetime

User = get_user_model()

class VideoShopConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get user from scope
        self.user = self.scope.get('user', AnonymousUser())
        
        # Add to video shop group
        await self.channel_layer.group_add(
            "video_shop",
            self.channel_name
        )
        await self.accept()
        
        # Send initial video content and live streams
        await self.send_initial_content()

    async def disconnect(self, close_code):
        # Remove from video shop group
        await self.channel_layer.group_discard(
            "video_shop",
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if not isinstance(self.user, AnonymousUser):
                if message_type == 'get_product_details':
                    await self.handle_product_details(data)
                elif message_type == 'add_to_cart':
                    await self.handle_add_to_cart(data)
                elif message_type == 'save_for_later':
                    await self.handle_save_for_later(data)
                elif message_type == 'request_next_video':
                    await self.handle_next_video()
                elif message_type == 'request_previous_video':
                    await self.handle_previous_video()
                elif message_type == 'start_stream':
                    await self.handle_start_stream(data)
                elif message_type == 'stream_interaction':
                    await self.handle_stream_interaction(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Authentication required'
                }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    @database_sync_to_async
    def get_initial_content(self):
        videos = VideoContent.objects.filter(is_active=True).order_by('-created_at')[:10]
        live_streams = LiveStream.objects.filter(is_live=True).order_by('-viewer_count')[:8]
        
        return {
            'videos': [self._format_video(video) for video in videos],
            'streams': [self._format_stream(stream) for stream in live_streams]
        }

    async def send_initial_content(self):
        content = await self.get_initial_content()
        await self.send(text_data=json.dumps({
            'type': 'initial_content',
            'content': content,
            'user': self.user.username if not isinstance(self.user, AnonymousUser) else None
        }))

    @database_sync_to_async
    def get_product_details(self, product_id):
        try:
            product = Product.objects.get(id=product_id)
            return {
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'description': product.description,
                'image': product.image.url if product.image else None,
                'stock': product.stock,
                'category': product.category.name if product.category else None,
                'vendor': {
                    'name': product.vendor.name,
                    'rating': product.vendor.rating
                } if product.vendor else None
            }
        except ObjectDoesNotExist:
            return None

    async def handle_product_details(self, data):
        product_id = data.get('product_id')
        product = await self.get_product_details(product_id)
        
        if product:
            await self.send(text_data=json.dumps({
                'type': 'product_details',
                'product': product
            }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Product not found'
            }))

    @database_sync_to_async
    def add_to_cart(self, product_id):
        try:
            product = Product.objects.get(id=product_id)
            # Add to cart logic here
            return True
        except ObjectDoesNotExist:
            return False

    async def handle_add_to_cart(self, data):
        product_id = data.get('product_id')
        success = await self.add_to_cart(product_id)
        
        await self.send(text_data=json.dumps({
            'type': 'cart_update',
            'success': success,
            'message': 'Product added to cart' if success else 'Failed to add product'
        }))

    @database_sync_to_async
    def save_for_later(self, product_id):
        try:
            product = Product.objects.get(id=product_id)
            # Save for later logic here
            return True
        except ObjectDoesNotExist:
            return False

    async def handle_save_for_later(self, data):
        product_id = data.get('product_id')
        success = await self.save_for_later(product_id)
        
        await self.send(text_data=json.dumps({
            'type': 'saved_item',
            'success': success,
            'message': 'Product saved for later' if success else 'Failed to save product'
        }))

    @database_sync_to_async
    def get_next_video(self):
        # Logic to get next video based on current video and user preferences
        video = VideoContent.objects.filter(is_active=True).first()
        return self._format_video(video) if video else None

    async def handle_next_video(self):
        video = await self.get_next_video()
        if video:
            await self.send(text_data=json.dumps({
                'type': 'new_video',
                'video': video
            }))

    @database_sync_to_async
    def get_previous_video(self):
        # Logic to get previous video
        video = VideoContent.objects.filter(is_active=True).first()
        return self._format_video(video) if video else None

    async def handle_previous_video(self):
        video = await self.get_previous_video()
        if video:
            await self.send(text_data=json.dumps({
                'type': 'new_video',
                'video': video
            }))

    @database_sync_to_async
    def start_stream(self, stream_data):
        try:
            # Create new live stream
            stream = LiveStream.objects.create(
                title=stream_data.get('title'),
                description=stream_data.get('description'),
                vendor=self.scope['user'].vendor,
                is_live=True
            )
            
            # Add featured products
            product_ids = stream_data.get('products', [])
            products = Product.objects.filter(id__in=product_ids)
            stream.featured_products.add(*products)
            
            return self._format_stream(stream)
        except Exception as e:
            return None

    async def handle_start_stream(self, data):
        stream_data = data.get('stream_data')
        stream = await self.start_stream(stream_data)
        
        if stream:
            # Notify all users in the group about new stream
            await self.channel_layer.group_send(
                "video_shop",
                {
                    'type': 'stream_update',
                    'stream': stream
                }
            )
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to start stream'
            }))

    async def handle_stream_interaction(self, data):
        # Handle various stream interactions (comments, reactions, etc.)
        await self.channel_layer.group_send(
            "video_shop",
            {
                'type': 'stream_interaction',
                'data': data
            }
        )

    async def stream_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'stream_update',
            'stream': event['stream']
        }))

    async def stream_interaction(self, event):
        await self.send(text_data=json.dumps({
            'type': 'stream_interaction',
            'data': event['data']
        }))

    def _format_video(self, video):
        return {
            'id': video.id,
            'url': video.video_file.url,
            'thumbnail': video.thumbnail.url if video.thumbnail else None,
            'title': video.title,
            'description': video.description,
            'duration': video.duration,
            'view_count': video.view_count,
            'created_at': video.created_at.isoformat(),
            'products': [{
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'image': product.image.url if product.image else None,
                'position': {
                    'x': tag.position_x,
                    'y': tag.position_y
                }
            } for product, tag in video.product_tags.items()]
        }

    def _format_stream(self, stream):
        return {
            'id': stream.id,
            'title': stream.title,
            'description': stream.description,
            'thumbnail': stream.thumbnail.url if stream.thumbnail else None,
            'vendor_name': stream.vendor.name,
            'viewers': stream.viewer_count,
            'duration': (datetime.now() - stream.started_at).total_seconds() if stream.started_at else 0,
            'category': stream.category.name if stream.category else 'Uncategorized',
            'featured_products': [{
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'image': product.image.url if product.image else None
            } for product in stream.featured_products.all()]
        }

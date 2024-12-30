import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from openai import AsyncOpenAI
from django.conf import settings
from products.models import Product, Category, Brand
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from django.db.models import Q
from asgiref.sync import sync_to_async
from decimal import Decimal
from datetime import datetime, timedelta

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Get user from scope
        self.user = self.scope.get('user', AnonymousUser())
        
        # Add to room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message', '')
            message_type = data.get('type', 'chat_message')

            # Process different types of messages
            if message_type == 'chat_message':
                # Process regular chat message
                response = await self.process_chat_message(message)
            elif message_type == 'product_search':
                # Process product search
                response = await self.search_products(message)
            elif message_type == 'add_to_cart':
                # Process add to cart request
                product_id = data.get('product_id')
                quantity = data.get('quantity', 1)
                response = await self.add_to_cart(product_id, quantity)
            else:
                response = "Unsupported message type"

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': response,
                    'user': self.user.username if not isinstance(self.user, AnonymousUser) else 'Anonymous'
                }
            )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid message format'
            }))

    async def chat_message(self, event):
        message = event['message']
        user = event.get('user', 'Anonymous')
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user': user
        }))

    async def process_chat_message(self, message):
        try:
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            chat_completion = await client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful shopping assistant for an African e-commerce platform. Help customers find products and make purchase decisions."},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"I apologize, but I'm having trouble processing your request. Please try again. Error: {str(e)}"

    @sync_to_async
    def search_products(self, query):
        try:
            # Search in products
            products = Product.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(brand__name__icontains=query)
            ).distinct()[:5]  # Limit to 5 results

            if not products:
                return "I couldn't find any products matching your search. Please try different keywords."

            # Format response
            response = "Here are some products that match your search:\n\n"
            for product in products:
                response += f"- {product.name} (${product.price})\n"
                response += f"  Description: {product.description[:100]}...\n\n"

            return response
        except Exception as e:
            return f"Error searching for products: {str(e)}"

    @sync_to_async
    def add_to_cart(self, product_id, quantity=1):
        try:
            # Get or create cart for the user
            cart, created = Cart.objects.get_or_create(user=self.user)
            
            # Get the product
            product = Product.objects.get(id=product_id)
            
            # Check if product is in stock
            if product.stock < quantity:
                return f"Sorry, only {product.stock} units of {product.name} are available."
            
            # Add to cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return f"Added {quantity} x {product.name} to your cart."
        except Product.DoesNotExist:
            return "Product not found."
        except Exception as e:
            return f"Error adding to cart: {str(e)}"

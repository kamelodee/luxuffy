from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from products.models import Product
from vendors.models import Vendor
from .models import VideoContent, LiveStream

# Create your views here.

@login_required
def chat_room(request, room_name):
    return render(request, 'chat_to_shop/chat_room.html', {
        'room_name': room_name,
        'user': request.user
    })

def chat_home(request):
    return render(request, 'chat_to_shop/chat_home.html')

@login_required
def video_shop_view(request):
    # Get active video content
    videos = VideoContent.objects.filter(is_active=True).order_by('-created_at')
    
    # Get active live streams
    live_streams = LiveStream.objects.filter(
        Q(status='live') & Q(is_active=True)
    ).select_related('vendor').order_by('-viewer_count')
    
    # Get featured products
    featured_products = Product.objects.filter(
        is_featured=True,
        is_active=True
    ).select_related('vendor')[:10]
    
    context = {
        'videos': videos,
        'live_streams': live_streams,
        'featured_products': featured_products,
    }
    
    return render(request, 'video_shop/video_feed.html', context)

@login_required
def vendor_dashboard(request):
    # Get vendor's videos and streams
    vendor = request.user.vendor
    videos = VideoContent.objects.filter(vendor=vendor).order_by('-created_at')
    streams = LiveStream.objects.filter(vendor=vendor).order_by('-created_at')
    
    # Get analytics data
    total_views = sum(video.view_count for video in videos)
    total_stream_views = sum(stream.total_views for stream in streams)
    total_interactions = sum(video.interaction_count for video in videos)
    
    context = {
        'vendor': vendor,
        'videos': videos,
        'streams': streams,
        'analytics': {
            'total_views': total_views,
            'total_stream_views': total_stream_views,
            'total_interactions': total_interactions,
        }
    }
    
    return render(request, 'video_shop/vendor_dashboard.html', context)

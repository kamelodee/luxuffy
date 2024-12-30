from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.db.models import Count, Avg
from ..models.video_shop import VideoContent, LiveStream, StreamAnalytics
from django.utils import timezone
from datetime import timedelta

@login_required
def video_shop_view(request):
    """
    Main view for the video shopping experience.
    Shows curated video content and live streams.
    """
    featured_videos = VideoContent.objects.filter(
        active=True
    ).select_related(
        'vendor', 'category'
    ).prefetch_related(
        'product_tags'
    ).order_by('-created_at')[:10]

    live_streams = LiveStream.objects.filter(
        is_live=True
    ).select_related(
        'vendor', 'category'
    ).prefetch_related(
        'featured_products'
    ).order_by('-viewer_count')[:8]

    context = {
        'featured_videos': featured_videos,
        'live_streams': live_streams,
        'is_vendor': hasattr(request.user, 'vendor')
    }
    
    return render(request, 'video_shop/video_feed.html', context)

def is_vendor(user):
    """Check if user is a vendor"""
    return hasattr(user, 'vendor')

@login_required
@user_passes_test(is_vendor)
def vendor_dashboard(request):
    """
    Dashboard for vendors to manage their video content and live streams.
    Shows analytics and allows starting new streams.
    """
    vendor = request.user.vendor
    
    # Get vendor's videos and streams
    videos = VideoContent.objects.filter(
        vendor=vendor
    ).annotate(
        product_count=Count('product_tags')
    ).order_by('-created_at')

    past_streams = LiveStream.objects.filter(
        vendor=vendor,
        is_live=False,
        ended_at__isnull=False
    ).select_related('analytics').order_by('-ended_at')

    # Calculate analytics
    total_views = sum(video.view_count for video in videos)
    avg_duration = videos.aggregate(Avg('duration'))['duration__avg'] or 0
    
    # Get analytics for past streams
    stream_analytics = StreamAnalytics.objects.filter(
        stream__vendor=vendor,
        stream__ended_at__isnull=False
    ).aggregate(
        total_revenue=Sum('revenue'),
        avg_viewers=Avg('peak_viewers'),
        total_engagement=Sum('total_views')
    )

    # Get recent performance (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_performance = StreamAnalytics.objects.filter(
        stream__vendor=vendor,
        stream__ended_at__gte=thirty_days_ago
    ).aggregate(
        revenue=Sum('revenue'),
        views=Sum('total_views'),
        avg_watch_time=Avg('average_watch_time')
    )

    context = {
        'videos': videos,
        'past_streams': past_streams,
        'analytics': {
            'total_views': total_views,
            'avg_duration': round(avg_duration, 2),
            'total_revenue': stream_analytics['total_revenue'] or 0,
            'avg_viewers': round(stream_analytics['avg_viewers'] or 0, 2),
            'total_engagement': stream_analytics['total_engagement'] or 0
        },
        'recent_performance': {
            'revenue': recent_performance['revenue'] or 0,
            'views': recent_performance['views'] or 0,
            'avg_watch_time': round(recent_performance['avg_watch_time'] or 0, 2)
        }
    }
    
    return render(request, 'video_shop/vendor_dashboard.html', context)

@login_required
@user_passes_test(is_vendor)
def upload_video(request):
    """Handle video upload for vendors"""
    if request.method == 'POST':
        try:
            video = VideoContent.objects.create(
                title=request.POST['title'],
                description=request.POST['description'],
                video_file=request.FILES['video'],
                thumbnail=request.FILES.get('thumbnail'),
                vendor=request.user.vendor,
                category_id=request.POST.get('category'),
                duration=int(request.POST['duration'])
            )
            
            # Process product tags
            product_tags = request.POST.getlist('product_tags')
            for tag in product_tags:
                tag_data = json.loads(tag)
                ProductTag.objects.create(
                    video=video,
                    product_id=tag_data['product_id'],
                    position_x=tag_data['x'],
                    position_y=tag_data['y'],
                    timestamp=tag_data.get('timestamp')
                )
            
            return JsonResponse({
                'success': True,
                'video_id': video.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    }, status=405)

@login_required
@user_passes_test(is_vendor)
def stream_analytics_api(request, stream_id):
    """API endpoint for stream analytics"""
    try:
        analytics = StreamAnalytics.objects.get(stream_id=stream_id)
        return JsonResponse({
            'success': True,
            'analytics': {
                'peak_viewers': analytics.peak_viewers,
                'total_views': analytics.total_views,
                'average_watch_time': analytics.average_watch_time,
                'engagement_rate': analytics.engagement_rate,
                'product_clicks': analytics.product_clicks,
                'revenue': float(analytics.revenue)
            }
        })
    except StreamAnalytics.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Analytics not found'
        }, status=404)

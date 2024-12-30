from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import JSONParser
from .models import Review
from .serializers import ReviewSerializer
from rest_framework import status

@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_review_list_create(request):
    """
    API: List all reviews for a product/vendor or create a new review.
    """
    if request.method == 'GET':
        content_type = request.GET.get('content_type')
        object_id = request.GET.get('object_id')

        if content_type and object_id:
            try:
                content_type_obj = ContentType.objects.get(model=content_type)
                reviews = Review.objects.filter(
                    content_type=content_type_obj, object_id=object_id, status='approved'
                )
            except ContentType.DoesNotExist:
                return JsonResponse({'error': 'Invalid content type'}, status=400)
        else:
            reviews = Review.objects.filter(status='approved')

        serializer = ReviewSerializer(reviews, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        content_type = data.get('content_type')
        object_id = data.get('object_id')

        try:
            content_type_obj = ContentType.objects.get(model=content_type)
        except ContentType.DoesNotExist:
            return JsonResponse({'error': 'Invalid content type'}, status=400)

        serializer = ReviewSerializer(data=data)
        if serializer.is_valid():
            serializer.save(
                user=request.user,
                content_type=content_type_obj,
                object_id=object_id,
                status='pending',
            )
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)

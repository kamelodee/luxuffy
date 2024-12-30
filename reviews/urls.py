from django.urls import path
from .views import review_list, add_review, moderate_review
from .api_views import api_review_list_create

urlpatterns = [
    # Template views
    path('reviews/<str:content_type>/<int:object_id>/', review_list, name='review_list'),
    path('reviews/<str:content_type>/<int:object_id>/add/', add_review, name='add_review'),
    path('reviews/<int:review_id>/moderate/', moderate_review, name='moderate_review'),

    # API views
    path('api/reviews/', api_review_list_create, name='api_review_list_create'),
]

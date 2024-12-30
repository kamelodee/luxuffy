from django.contrib import admin
from .models import Review, ReviewImage


@admin.register(Review)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'object_id', 'rating', 'status', 'created_at')
    list_filter = ('content_type', 'rating', 'status', 'created_at')
    search_fields = ('user__username', 'title', 'comment')
    actions = ['approve_reviews', 'reject_reviews']

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        queryset.update(status='approved')

    @admin.action(description="Reject selected reviews")
    def reject_reviews(self, request, queryset):
        queryset.update(status='rejected')

@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ('review', 'image', 'uploaded_at')

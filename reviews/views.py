from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Review
from .forms import ReviewForm

@login_required
def review_list(request, content_type, object_id):
    """
    Display approved reviews for a specific product or vendor.
    """
    content_type_obj = get_object_or_404(ContentType, model=content_type)
    reviews = Review.objects.filter(content_type=content_type_obj, object_id=object_id, status='approved')
    context = {'reviews': reviews, 'content_type': content_type, 'object_id': object_id}
    return render(request, 'reviews/review_list.html', context)

@login_required
def add_review(request, content_type, object_id):
    """
    Allow users to add a review for a product or vendor.
    """
    content_type_obj = get_object_or_404(ContentType, model=content_type)
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.content_type = content_type_obj
            review.object_id = object_id
            review.status = 'pending'  # New reviews default to "Pending"
            review.save()
            return redirect('review_list', content_type=content_type, object_id=object_id)
    else:
        form = ReviewForm()
    return render(request, 'reviews/add_review.html', {'form': form, 'content_type': content_type, 'object_id': object_id})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def moderate_review(request, review_id):
    """
    Approve or reject a review (Admin only).
    """
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            review.status = 'approved'
        elif action == 'reject':
            review.status = 'rejected'
        review.save()
        return redirect('review_list', content_type=review.content_type.model, object_id=review.object_id)
    return render(request, 'reviews/moderate_review.html', {'review': review})

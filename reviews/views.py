from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from catalog.models import Product

from .forms import ReviewForm
from .models import Review


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
    return redirect("store:product_detail", slug=product.slug)

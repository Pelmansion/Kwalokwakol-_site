from django.shortcuts import get_object_or_404, render

from .models import StaticPage


def page_detail(request, slug):
    page = get_object_or_404(StaticPage, slug=slug, is_active=True)
    return render(request, "content/page.html", {"page": page})

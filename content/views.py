from types import SimpleNamespace

from django.http import Http404
from django.shortcuts import render

from kwalo.static_pages import STATIC_PAGES

from .models import StaticPage


def _fallback_static_page(slug: str):
    for page_def in STATIC_PAGES:
        if page_def["slug"] == slug:
            return SimpleNamespace(
                title=page_def["title"],
                content=page_def["content"](),
                slug=slug,
            )
    return None


def page_detail(request, slug):
    try:
        page = StaticPage.objects.get(slug=slug, is_active=True)
    except StaticPage.DoesNotExist:
        page = _fallback_static_page(slug)
        if page is None:
            raise Http404
    return render(request, "content/page.html", {"page": page})

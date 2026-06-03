"""URLs fiables pour les fichiers uploadés (profil, produits, culture…)."""

from __future__ import annotations

from urllib.parse import quote

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

_PLACEHOLDER = "/static/images/icons/icon-192.png"


def _cache_bust(url: str, token: str) -> str:
    if not url or not token:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}v={quote(token, safe='')}"


@register.filter
def file_url(file_field):
    """URL absolue ou racine du site pour un ImageField / FileField."""
    try:
        if not file_field:
            return ""
        try:
            url = file_field.url
        except (ValueError, AttributeError, OSError):
            return ""
        if not url:
            return ""
        if not url.startswith(("http://", "https://", "/")):
            url = f"{settings.MEDIA_URL.rstrip('/')}/{url.lstrip('/')}"
        storage_name = getattr(file_field, "name", None) or ""
        token = storage_name or url.rsplit("/", 1)[-1]
        return _cache_bust(url, token)
    except Exception:
        return ""


def get_product_image_url(product):
    """Image produit : fichier uploadé, média, puis URL externe."""
    try:
        if not product:
            return ""
        image = getattr(product, "image", None)
        if image and getattr(image, "name", None):
            u = file_url(image)
            if u:
                return u
        if hasattr(product, "media"):
            media = product.media.filter(is_primary=True).first() or product.media.first()
            if media and getattr(media, "url", None):
                return _cache_bust(media.url, f"media-{media.pk}")
        return (getattr(product, "image_url", None) or "").strip()
    except Exception:
        return ""


@register.simple_tag
def product_image_url(product):
    return get_product_image_url(product)


@register.simple_tag
def img_onerror_attr():
    """Attribut HTML onerror vers une icône de secours (usage : {% img_onerror_attr %})."""
    return mark_safe(f'onerror="this.onerror=null;this.src=\'{_PLACEHOLDER}\';"')

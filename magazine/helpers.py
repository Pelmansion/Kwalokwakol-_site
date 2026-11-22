"""Helpers d'affichage public Dan Prestige Magazine."""

from __future__ import annotations

from django.conf import settings


def public_queryset(qs, *, demo_field: str = "is_demo"):
    """En production (DEBUG=False), exclut les contenus de démonstration."""
    if settings.DEBUG:
        return qs
    if hasattr(qs.model, demo_field):
        return qs.filter(**{demo_field: False})
    return qs


def reading_time_minutes(text: str) -> int:
    words = len((text or "").split())
    return max(1, round(words / 200)) if words else 1


def whatsapp_share_url(text: str, url: str = "") -> str:
    from urllib.parse import quote

    from kwalo.contact_info import KOLE_WHATSAPP_WA_ME

    payload = f"{text}\n{url}".strip() if url else text
    return f"https://wa.me/?text={quote(payload)}"

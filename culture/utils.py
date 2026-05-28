from __future__ import annotations

import io

import qrcode
import qrcode.image.svg
from django.core.exceptions import PermissionDenied

from marketplace.models import ServiceProvider, Vendor

from .models import ArtistProfile


def generate_qr_svg(data: str, *, size: int = 240) -> str:
    """Renvoie un QR code SVG (string) prêt à intégrer en HTML.

    Le SVG est inline donc pas besoin de stockage fichier.
    """
    factory = qrcode.image.svg.SvgImage
    img = qrcode.make(data, image_factory=factory, box_size=10, border=2)
    buffer = io.BytesIO()
    img.save(buffer)
    svg = buffer.getvalue().decode("utf-8")
    # On force la taille via attribut width/height
    if "<svg " in svg and "width=" not in svg.split(">", 1)[0]:
        svg = svg.replace("<svg ", f'<svg width="{size}" height="{size}" ', 1)
    return svg


def user_can_become_artist(user) -> bool:
    """Pour activer un profil artiste il faut être vendeur OU prestataire."""
    if not user.is_authenticated:
        return False
    return (
        Vendor.objects.filter(owner=user).exists()
        or ServiceProvider.objects.filter(owner=user).exists()
    )


def get_artist_or_redirect(user):
    """Renvoie l'ArtistProfile de l'utilisateur, ou None si pas encore créé."""
    if not user.is_authenticated:
        return None
    return ArtistProfile.objects.filter(user=user).first()


def require_artist(user) -> ArtistProfile:
    """Lève PermissionDenied si l'user n'a pas de profil artiste."""
    artist = get_artist_or_redirect(user)
    if not artist or not artist.is_active:
        raise PermissionDenied("Profil artiste inactif ou inexistant.")
    return artist


def require_artist_or_redirect(request):
    """Alias pour toutes les vues espace artiste (évite PermissionDenied → 500)."""
    return resolve_artist_for_dashboard(request)


def resolve_artist_for_dashboard(request):
    """
    Renvoie (artist, redirect_response).
    Redirection claire si profil artiste absent ou inactif (évite PermissionDenied / 500).
    """
    from django.contrib import messages
    from django.shortcuts import redirect

    user = request.user
    artist = get_artist_or_redirect(user)
    if not artist:
        if user_can_become_artist(user):
            messages.info(
                request,
                "Activez votre profil artiste pour accéder à l'espace artiste.",
            )
            return None, redirect("culture:artist_activate")
        messages.error(request, "Cet espace est réservé aux vendeurs et prestataires artistes.")
        return None, redirect("culture:home")
    if not artist.is_active:
        messages.info(request, "Réactivez votre profil artiste pour accéder à cet espace.")
        return None, redirect("culture:artist_activate")
    return artist, None

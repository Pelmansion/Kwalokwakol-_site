from django import template

from culture.models import ArtistProfile
from culture.utils import user_can_become_artist

register = template.Library()


@register.filter
def is_artist(user) -> bool:
    """True si l'utilisateur a un profil artiste actif."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return ArtistProfile.objects.filter(user=user, is_active=True).exists()


@register.filter
def can_become_artist(user) -> bool:
    """True si l'utilisateur peut activer un profil artiste (vendeur/prestataire)."""
    return user_can_become_artist(user)

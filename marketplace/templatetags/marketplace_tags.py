from django import template

from marketplace.models import ServiceProvider, Vendor
from accounts.models import UserProfile

register = template.Library()


@register.filter
def is_vendor(user):
    if not user or not user.is_authenticated:
        return False
    return Vendor.objects.filter(owner=user).exists()


@register.filter
def is_service_provider(user):
    if not user or not user.is_authenticated:
        return False
    return ServiceProvider.objects.filter(owner=user).exists()


@register.filter
def is_app_admin(user):
    """
    Retourne True si l'utilisateur est admin ou super admin de l'application.
    """
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        return False
    return profile.role in (UserProfile.ROLE_ADMIN, UserProfile.ROLE_SUPER_ADMIN)


@register.filter
def is_client(user):
    """
    Retourne True si l'utilisateur est un client (ni admin, ni vendeur, ni prestataire).
    Seuls les clients peuvent passer des commandes et voir l'accueil boutique.
    """
    if not user or not user.is_authenticated:
        return False
    if is_vendor(user) or is_service_provider(user) or is_app_admin(user):
        return False
    return True

from django import template

from marketplace.models import ServiceProvider, Vendor
from accounts.models import UserProfile
from store.templatetags.media_tags import register as _media_register

register = template.Library()
# Tags médias (file_url, product_image_url…) disponibles avec {% load marketplace_tags %}
register.filters.update(_media_register.filters)
register.tags.update(_media_register.tags)


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


def _norm_request_path(path):
    """Chemin comparable (sans slash final sauf racine)."""
    if not path:
        return "/"
    path = path.strip()
    if not path or path == "/":
        return "/"
    return path.rstrip("/") or "/"


@register.simple_tag(takes_context=True)
def show_mobile_back_button(context):
    """
    True si le bouton « Retour » de la barre mobile doit être affiché.
    Masqué sur la page d'accueil du rôle (boutique / tableau de bord vendeur, etc.).
    """
    from django.urls import reverse

    request = context["request"]
    user = request.user
    cur = _norm_request_path(getattr(request, "path", "") or "/")

    if not user.is_authenticated:
        return cur != "/"

    if is_app_admin(user):
        home_url = reverse("accounts:admin_dashboard")
    elif is_vendor(user):
        home_url = reverse("marketplace:dashboard")
    elif is_service_provider(user):
        home_url = reverse("marketplace:service_provider_dashboard")
    else:
        home_url = reverse("store:home")

    home_path = _norm_request_path(home_url)
    return cur != home_path

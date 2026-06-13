"""Qui peut utiliser la boutique en tant qu'acheteur."""

from accounts.models import UserProfile


def user_can_shop_as_customer(user) -> bool:
    """
    True si l'utilisateur peut commander, réserver et utiliser le panier.
    Les vendeurs et prestataires peuvent aussi acheter chez d'autres pros.
    Seuls les comptes administration sont exclus.
    """
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return False
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile.role not in (UserProfile.ROLE_ADMIN, UserProfile.ROLE_SUPER_ADMIN)

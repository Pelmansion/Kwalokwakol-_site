"""Profil utilisateur disponible dans tous les templates (après connexion)."""

from .models import UserProfile


def user_profile(request):
    """
    Associe le UserProfile au compte connecté (création paresseuse si besoin)
    pour afficher photo de profil et couverture partout sans erreur OneToOne.
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"user_profile": None}
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return {"user_profile": profile}

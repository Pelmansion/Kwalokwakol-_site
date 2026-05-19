"""Authentification par nom d'utilisateur, e-mail ou numéro (profil)."""

from __future__ import annotations

import re

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


def _digits_only(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def resolve_login_to_user(raw: str) -> User | None:
    """Retrouve un utilisateur à partir d'un identifiant saisi à la connexion."""
    raw = (raw or "").strip()
    if not raw:
        return None
    if "@" in raw:
        return User.objects.filter(email__iexact=raw).first()
    user = User.objects.filter(username__iexact=raw).first()
    if user:
        return user
    digits = _digits_only(raw)
    if len(digits) < 8:
        return None
    from accounts.models import UserProfile

    for prof in UserProfile.objects.select_related("user").filter(phone__gt=""):
        p = _digits_only(prof.phone)
        if not p:
            continue
        if p == digits or p.endswith(digits[-10:]) or digits.endswith(p[-10:]):
            return prof.user
    return None


class EmailPhoneUsernameBackend(ModelBackend):
    """Accepte e-mail, nom d'utilisateur ou numéro (UserProfile.phone)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or password is None:
            return None
        user = resolve_login_to_user(username)
        if user is None:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

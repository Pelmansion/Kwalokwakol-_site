"""
Envoi d'emails pour la vérification d'inscription.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.template.loader import render_to_string
from django.urls import reverse
from urllib.parse import quote

SALT = "email-verification"


def make_verification_token(user):
    """Génère un token signé pour la vérification d'email (expire selon settings.EMAIL_VERIFICATION_MAX_AGE)."""
    signer = TimestampSigner(salt=SALT)
    return signer.sign(user.pk)


def get_user_from_token(token):
    """
    Décode le token et retourne l'utilisateur si valide.
    Retourne (user, None) en cas de succès, (None, "message_erreur") sinon.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    signer = TimestampSigner(salt=SALT)
    max_age = getattr(settings, "EMAIL_VERIFICATION_MAX_AGE", 48 * 3600)
    try:
        user_id = signer.unsign(token, max_age=max_age)
        user = User.objects.filter(pk=int(user_id)).first()
        if not user:
            return None, "Utilisateur introuvable."
        return user, None
    except (SignatureExpired, BadSignature):
        return None, "Lien expiré ou invalide. Demandez un nouvel email de vérification."


def send_verification_email(request, user):
    """Envoie l'email de vérification à l'utilisateur après inscription."""
    token = make_verification_token(user)
    path = reverse("accounts:verify_email") + "?token=" + quote(token, safe="")
    verify_url = request.build_absolute_uri(path)

    subject = "Confirmez votre adresse email - Kwalo"
    body = render_to_string(
        "accounts/emails/verify_email.txt",
        {"user": user, "verify_url": verify_url},
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@kwalo.local")
    send_mail(
        subject,
        body,
        from_email,
        [user.email],
        fail_silently=False,
    )

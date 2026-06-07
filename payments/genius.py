"""
Client HTTP GeniusPay (https://pay.genius.ci/docs/api).
Les clés ne doivent jamais figurer dans le code : variables d'environnement uniquement.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from decimal import Decimal
from typing import Any
from urllib.parse import quote

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

MERCHANT_API_BASE = "https://pay.genius.ci/api/v1/merchant"


class GeniusPaymentError(Exception):
    """Erreur API GeniusPay ou réponse inattendue."""


GENIUS_UNAVAILABLE_USER_MSG = (
    "Le paiement en ligne n'est pas disponible pour le moment. "
    "Réessayez plus tard ou contactez le support Kolê."
)


def is_configured() -> bool:
    key = (getattr(settings, "GENIUS_API_KEY", None) or "").strip()
    secret = (getattr(settings, "GENIUS_API_SECRET", None) or "").strip()
    return bool(key and secret)


def genius_credential_mode() -> str:
    """
    GeniusPay utilise la même URL d'API ; l'environnement est déterminé par les clés :
    pk_sandbox_ / sk_sandbox_ → tests (aucun encaissement réel) ;
    pk_live_ / sk_live_ → production.
    """
    key = (getattr(settings, "GENIUS_API_KEY", None) or "").strip().lower()
    if key.startswith("pk_live_"):
        return "live"
    if key.startswith("pk_sandbox_"):
        return "sandbox"
    return "unknown"


def is_sandbox_credentials() -> bool:
    return genius_credential_mode() == "sandbox"


def _headers() -> dict[str, str]:
    return {
        "X-API-Key": settings.GENIUS_API_KEY.strip(),
        "X-API-Secret": settings.GENIUS_API_SECRET.strip(),
        "Content-Type": "application/json",
    }


def _amount_xof(amount: Decimal | float | str) -> int:
    """Montant entier en XOF (minimum API : 200)."""
    v = int(Decimal(str(amount)).quantize(Decimal("1")))
    if v < 200:
        raise GeniusPaymentError("Le montant minimum pour GeniusPay est de 200 FCFA.")
    return v


def create_checkout_payment(
    *,
    amount: Decimal | float,
    description: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    metadata: dict[str, str],
    success_url: str,
    error_url: str,
) -> dict[str, Any]:
    """
    Crée un paiement sans payment_method → checkout Genius (Wave, OM, MTN, carte…).
    Retourne au minimum checkout_url et reference.
    """
    if not is_configured():
        raise GeniusPaymentError("GeniusPay n'est pas configuré (clés API manquantes).")

    country = (getattr(settings, "GENIUS_DEFAULT_COUNTRY", None) or "CI").strip()
    payload: dict[str, Any] = {
        "amount": _amount_xof(amount),
        "currency": "XOF",
        "description": (description or "Commande")[:500],
        "customer": {
            "name": (customer_name or "Client")[:200],
            "email": customer_email or "",
            "phone": customer_phone or "",
            "country": country,
        },
        "metadata": metadata,
        "success_url": success_url,
        "error_url": error_url,
    }

    try:
        r = requests.post(
            f"{MERCHANT_API_BASE}/payments",
            headers=_headers(),
            json=payload,
            timeout=45,
        )
    except requests.RequestException as e:
        logger.exception("GeniusPay réseau: %s", e)
        raise GeniusPaymentError("Réseau indisponible vers GeniusPay.") from e

    try:
        body = r.json()
    except ValueError:
        logger.warning("GeniusPay réponse non-JSON: %s", r.text[:500])
        raise GeniusPaymentError("Réponse GeniusPay invalide.")

    if r.status_code not in (200, 201) or not body.get("success"):
        msg = body.get("message") or body.get("error") or r.text[:200]
        logger.warning("GeniusPay création refusée: %s %s", r.status_code, body)
        raise GeniusPaymentError(str(msg) if msg else "Création du paiement refusée.")

    data = body.get("data") or {}
    checkout_url = data.get("checkout_url") or data.get("payment_url")
    if not checkout_url:
        raise GeniusPaymentError("Réponse GeniusPay sans URL de paiement.")

    return {
        "checkout_url": checkout_url,
        "reference": data.get("reference") or "",
        "id": data.get("id"),
        "raw": data,
    }


def initiate_checkout(
    *,
    amount: Decimal | float,
    description: str,
    customer_name: str,
    customer_email: str = "",
    customer_phone: str = "",
    metadata: dict[str, str] | None = None,
    success_url: str,
    error_url: str,
) -> dict[str, Any]:
    """
    Point d'entrée unique pour ouvrir le checkout GeniusPay
    (abonnements, commandes boutique, musique, billets).
    """
    if not is_configured():
        raise GeniusPaymentError(GENIUS_UNAVAILABLE_USER_MSG)
    res = create_checkout_payment(
        amount=amount,
        description=description,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        metadata=metadata or {},
        success_url=success_url,
        error_url=error_url,
    )
    if not res.get("checkout_url"):
        raise GeniusPaymentError("Réponse GeniusPay sans URL de paiement.")
    return res


def fetch_payment(reference: str) -> dict[str, Any]:
    """GET /payments/{reference} — statut completed / pending / failed."""
    if not is_configured():
        raise GeniusPaymentError("GeniusPay n'est pas configuré.")
    if not reference:
        raise GeniusPaymentError("Référence manquante.")

    try:
        r = requests.get(
            f"{MERCHANT_API_BASE}/payments/{quote(reference, safe='')}",
            headers=_headers(),
            timeout=30,
        )
    except requests.RequestException as e:
        logger.exception("GeniusPay fetch: %s", e)
        raise GeniusPaymentError("Impossible de joindre GeniusPay.") from e

    try:
        body = r.json()
    except ValueError:
        raise GeniusPaymentError("Réponse invalide.")

    if r.status_code != 200 or not body.get("success"):
        logger.warning("GeniusPay fetch erreur: %s %s", r.status_code, body)
        raise GeniusPaymentError("Transaction introuvable ou erreur API.")

    return body.get("data") or {}


def verify_webhook_signature(body: bytes, timestamp: str, signature: str, secret: str) -> bool:
    """
    signature = HMAC-SHA256(hex) de (timestamp + '.' + corps brut JSON).
    Voir documentation GeniusPay « Sécurité des webhooks ».
    """
    if not secret or not signature or not timestamp:
        return False
    try:
        message = f"{timestamp}.{body.decode('utf-8')}"
    except UnicodeDecodeError:
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

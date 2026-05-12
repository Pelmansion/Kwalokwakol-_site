import logging

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class PaymentsConfig(AppConfig):
    name = "payments"

    def ready(self) -> None:
        if settings.DEBUG:
            return
        from payments.genius import genius_credential_mode, is_configured

        if not is_configured():
            logger.warning(
                "GeniusPay non configuré (GENIUS_API_KEY / GENIUS_API_SECRET absents ou vides). "
                "Le checkout n’affichera que le paiement à la livraison. "
                "Sur Render : Environment → ajoutez ces variables puis redeploy."
            )
        elif genius_credential_mode() == "sandbox":
            logger.warning(
                "GeniusPay : clés SANDBOX actives (pk_sandbox_ / sk_sandbox_). "
                "L’interface affichera « mode test » et aucun paiement réel. "
                "Pour la production : remplacez par pk_live_ et sk_live_ depuis le tableau Genius, "
                "plus GENIUS_WEBHOOK_SECRET en whsec_live_… pour le webhook live."
            )

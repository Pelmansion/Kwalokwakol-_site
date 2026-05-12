import logging

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class PaymentsConfig(AppConfig):
    name = "payments"

    def ready(self) -> None:
        if settings.DEBUG:
            return
        from payments.genius import is_configured

        if not is_configured():
            logger.warning(
                "GeniusPay non configuré (GENIUS_API_KEY / GENIUS_API_SECRET absents ou vides). "
                "Le checkout n’affichera que le paiement à la livraison. "
                "Sur Render : Environment → ajoutez ces variables puis redeploy."
            )

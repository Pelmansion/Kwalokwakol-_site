"""Règles d'annulation des réservations client (demandes de service)."""

from datetime import timedelta

from django.utils import timezone

from marketplace.models import ServiceRequest


def reservation_delete_deadline(created_at):
    """
    Annulation possible jusqu'au prochain midi (12h00, heure locale) :
    - demande avant midi → jusqu'à midi le même jour ;
    - demande à partir de midi → jusqu'à midi le lendemain.
    """
    local = timezone.localtime(created_at)
    noon_same_day = local.replace(hour=12, minute=0, second=0, microsecond=0)
    if local < noon_same_day:
        return noon_same_day
    return (local + timedelta(days=1)).replace(
        hour=12, minute=0, second=0, microsecond=0
    )


def can_client_delete_reservation(service_request) -> bool:
    if service_request.status != ServiceRequest.STATUS_PENDING:
        return False
    return timezone.now() < reservation_delete_deadline(service_request.created_at)

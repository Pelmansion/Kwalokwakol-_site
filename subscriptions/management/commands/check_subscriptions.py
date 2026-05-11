"""Marque les abonnements expirés comme past_due et notifie les titulaires."""
from django.core.management.base import BaseCommand
from django.utils import timezone

from notifications.models import Notification
from subscriptions.models import Subscription


class Command(BaseCommand):
    help = "Marque les abonnements dont la période est expirée comme past_due."

    def handle(self, *args, **options):
        now = timezone.now()
        expired = Subscription.objects.filter(
            status=Subscription.STATUS_ACTIVE,
            current_period_end__lte=now,
        )
        count = 0
        for sub in expired:
            sub.status = Subscription.STATUS_PAST_DUE
            sub.save(update_fields=["status", "updated_at"])
            count += 1

            owner_profile = sub.owner_profile
            if owner_profile and owner_profile.owner_id:
                Notification.objects.create(
                    user=owner_profile.owner,
                    title="Abonnement expiré",
                    body=(
                        f"Votre abonnement mensuel ({sub.monthly_amount} FCFA) a expiré. "
                        "Renouvelez-le pour continuer à accéder à votre espace."
                    ),
                    kind=Notification.WARNING if hasattr(Notification, "WARNING") else Notification.INFO,
                )

        self.stdout.write(self.style.SUCCESS(f"{count} abonnement(s) marqué(s) comme expirés."))

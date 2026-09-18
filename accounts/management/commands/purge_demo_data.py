"""
Supprime les données de démo / transactionnelles en production.

Conserve :
  - comptes admin et superadmin (par défaut : admin, superadmin)
  - catégories plateforme (sans vendeur / prestataire)
  - pages statiques non [DEMO]
  - formules d'abonnement (SubscriptionPlan)

Usage :
    python manage.py purge_demo_data --dry-run
    python manage.py purge_demo_data --confirm PURGE
"""

from __future__ import annotations

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from accounts.models import Address, Favorite
from catalog.category_utils import platform_categories_queryset
from catalog.models import Category, CategoryShowcaseImage, Product, ProductMedia, ProductVariant
from content.models import HomepageBackground, StaticPage
from culture.models import (
    ArtistProfile,
    Event,
    Song,
    SongPlay,
    SongPurchase,
    Ticket,
    TicketCategory,
)
from marketplace.models import ServiceProvider, ServiceRequest, Vendor
from messaging.models import Message, Thread
from notifications.models import Notification
from orders.models import Order, OrderItem, OrderStatusHistory
from payments.models import Payment
from reviews.models import Review, ReviewReply
from subscriptions.models import Subscription, SubscriptionPayment

User = get_user_model()

DEFAULT_KEEP = ("admin", "superadmin")


class Command(BaseCommand):
    help = "Purge les données de test et remet les compteurs métier à zéro (hors admin/superadmin)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            type=str,
            help='Obligatoire pour exécuter : --confirm PURGE',
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche ce qui serait supprimé sans modifier la base.",
        )
        parser.add_argument(
            "--keep-usernames",
            type=str,
            default=",".join(DEFAULT_KEEP),
            help="Comptes à conserver (séparés par des virgules).",
        )

    def handle(self, *args, **options):
        keep = {
            u.strip()
            for u in (options["keep_usernames"] or "").split(",")
            if u.strip()
        }
        if not keep:
            raise CommandError("Au moins un compte doit être conservé.")

        dry_run = options["dry_run"]
        if not dry_run and options.get("confirm") != "PURGE":
            raise CommandError(
                "Confirmation requise : python manage.py purge_demo_data --confirm PURGE"
            )

        engine = connection.settings_dict.get("ENGINE", "")
        if "sqlite" in engine and not dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Base SQLite détectée — utilisez DATABASE_URL PostgreSQL pour la prod."
                )
            )

        self.stdout.write(self.style.MIGRATE_HEADING("État avant purge"))
        self._print_counts(keep)

        if dry_run:
            self.stdout.write(self.style.WARNING("Mode dry-run — aucune modification."))
            return

        with transaction.atomic():
            counts = self._purge(keep)
            self._reset_sequences()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Purge terminée :"))
        for label, n in counts.items():
            if n:
                self.stdout.write(f"  • {label} : {n} supprimé(s)")

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("État après purge"))
        self._print_counts(keep)

    def _purge(self, keep: set[str]) -> dict[str, int]:
        stats: dict[str, int] = {}

        def track(label, result):
            n = result[0] if isinstance(result, tuple) else result
            stats[label] = stats.get(label, 0) + n
            return n

        track("ReviewReply", ReviewReply.objects.all().delete())
        track("SongPlay", SongPlay.objects.all().delete())
        track("SongPurchase", SongPurchase.objects.all().delete())
        track("Favorite", Favorite.objects.all().delete())
        track("ServiceRequest", ServiceRequest.objects.all().delete())
        track("Payment", Payment.objects.all().delete())
        track("OrderStatusHistory", OrderStatusHistory.objects.all().delete())
        track("OrderItem", OrderItem.objects.all().delete())
        track("Message", Message.objects.all().delete())
        track("SubscriptionPayment", SubscriptionPayment.objects.all().delete())
        track("Notification", Notification.objects.all().delete())
        track("Address", Address.objects.all().delete())

        track("Review", Review.objects.all().delete())
        track("Order", Order.objects.all().delete())
        track("Thread", Thread.objects.all().delete())
        track("Subscription", Subscription.objects.all().delete())
        track("Ticket", Ticket.objects.all().delete())
        track("ProductMedia", ProductMedia.objects.all().delete())
        track("ProductVariant", ProductVariant.objects.all().delete())
        track("Song", Song.objects.all().delete())
        track("CategoryShowcaseImage", CategoryShowcaseImage.objects.all().delete())
        track(
            "StaticPage [DEMO]",
            StaticPage.objects.filter(title__startswith="[DEMO]").delete(),
        )
        track("Product", Product.objects.all().delete())
        track("TicketCategory", TicketCategory.objects.all().delete())
        track("Event", Event.objects.all().delete())
        track("ArtistProfile", ArtistProfile.objects.all().delete())

        platform_ids = list(platform_categories_queryset().values_list("pk", flat=True))
        track(
            "Category (boutiques)",
            Category.objects.exclude(pk__in=platform_ids).delete(),
        )

        track("Vendor", Vendor.objects.all().delete())
        track("ServiceProvider", ServiceProvider.objects.all().delete())
        track("HomepageBackground", HomepageBackground.objects.all().delete())

        users_qs = User.objects.exclude(username__in=keep)
        track("User (hors admin)", users_qs.delete())

        return stats

    def _reset_sequences(self):
        if connection.vendor != "postgresql":
            return
        from django.core.management.color import no_style

        models = apps.get_models(include_auto_created=True)
        statements = connection.ops.sequence_reset_sql(no_style(), models)
        with connection.cursor() as cursor:
            for sql in statements:
                cursor.execute(sql)
        self.stdout.write("  Séquences PostgreSQL réinitialisées.")

    def _print_counts(self, keep: set[str]):
        self.stdout.write(f"  Utilisateurs conservés : {', '.join(sorted(keep))}")
        self.stdout.write(f"  Utilisateurs total     : {User.objects.count()}")
        self.stdout.write(f"  Vendeurs               : {Vendor.objects.count()}")
        self.stdout.write(
            f"  Prestataires           : {ServiceProvider.objects.count()}"
        )
        self.stdout.write(f"  Commandes              : {Order.objects.count()}")
        self.stdout.write(f"  Produits               : {Product.objects.count()}")
        self.stdout.write(
            f"  Catégories plateforme  : {platform_categories_queryset().count()}"
        )
        self.stdout.write(
            f"  Pages statiques        : {StaticPage.objects.exclude(title__startswith='[DEMO]').count()}"
        )

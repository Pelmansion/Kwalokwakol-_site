"""
Produits de démonstration pour Render / préprod.

Prérequis : au moins un vendeur lié à un utilisateur (ex. create_test_vendor).
Active l'abonnement du vendeur (requis pour l'affichage catalogue) puis crée 4 produits.

Usage (shell Render) :
  python manage.py render_demo_products
  python manage.py render_demo_products --vendor-id 3
"""

from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.models import Category, Product
from marketplace.models import Vendor
from subscriptions.models import Subscription
from subscriptions.utils import get_or_create_subscription_for_vendor

DEMO_ITEMS = [
    ("Riz local démo 5kg", 12500, 40, "Sac de riz — donnée de test pour le catalogue."),
    ("Huile rouge 1L démo", 3500, 60, "Huile de palme — test catalogue."),
    ("Attiéké 1kg démo", 800, 100, "Attiéké frais — test catalogue."),
    ("Pagne wax coupon démo", 15000, 15, "Coupon tissu — test catalogue."),
]


class Command(BaseCommand):
    help = "Crée 4 produits démo et active l'abonnement vendeur (visible sur le catalogue public)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--vendor-id",
            type=int,
            default=None,
            help="ID de la boutique. Par défaut : premier vendeur ayant un compte (owner).",
        )

    def handle(self, *args, **options):
        vendor_id = options.get("vendor_id")
        if vendor_id:
            vendor = Vendor.objects.filter(pk=vendor_id).first()
            if not vendor:
                self.stdout.write(self.style.ERROR(f"Aucun vendeur avec l'id {vendor_id}."))
                return
        else:
            vendor = Vendor.objects.exclude(owner__isnull=True).first()

        if not vendor:
            self.stdout.write(
                self.style.ERROR(
                    "Aucun vendeur avec propriétaire (owner). Créez-en un avec :\n"
                    "  python manage.py create_test_vendor"
                )
            )
            return

        sub = get_or_create_subscription_for_vendor(vendor)
        now = timezone.now()
        sub.status = Subscription.STATUS_ACTIVE
        if not sub.monthly_amount or sub.monthly_amount <= 0:
            sub.monthly_amount = 5000
        if not sub.started_at:
            sub.started_at = now
        sub.current_period_end = now + timedelta(days=365)
        sub.save(
            update_fields=[
                "status",
                "monthly_amount",
                "started_at",
                "current_period_end",
                "updated_at",
            ]
        )

        cat = (
            Category.objects.filter(
                vendor__isnull=True,
                service_provider__isnull=True,
                is_active=True,
            )
            .order_by("id")
            .first()
        )
        if not cat:
            cat = Category.objects.create(
                name="Démo catalogue Kolê",
                description="Catégorie auto pour produits de démonstration.",
                is_active=True,
            )

        n_created = 0
        n_updated = 0
        for i, (name, price, stock, desc) in enumerate(DEMO_ITEMS, start=1):
            slug = f"v{vendor.pk}-kwalo-render-demo-{i}"
            _obj, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    "vendor": vendor,
                    "service_provider": None,
                    "category": cat,
                    "name": name,
                    "description": desc,
                    "price": price,
                    "stock": stock,
                    "kind": Product.PRODUCT,
                    "is_active": True,
                    "image_url": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=600",
                    "location": (vendor.location or "Abidjan")[:200],
                },
            )
            if created:
                n_created += 1
            else:
                n_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Boutique #{vendor.pk} — {vendor.name}. Abonnement actif jusqu'au {sub.current_period_end.date()}."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Produits démo : {n_created} créé(s), {n_updated} mis à jour. Slugs : "
                f"v{vendor.pk}-kwalo-render-demo-1 … 4"
            )
        )
        self.stdout.write("Vérifier le catalogue : page d'accueil ou liste produits (hors compte vendeur).")

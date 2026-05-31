"""
Supprime la catégorie « Démo catalogue … » (ex. Kolê, KwaloK) affichée sur le site.

Usage :
  python manage.py remove_demo_catalogue_label
  python manage.py remove_demo_catalogue_label --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category, Product


class Command(BaseCommand):
    help = "Retire les catégories « Démo catalogue … » et réaffecte les produits."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche les actions sans modifier la base.",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        demo_cats = list(
            Category.objects.filter(name__icontains="Démo catalogue").filter(
                vendor__isnull=True,
                service_provider__isnull=True,
            )
        )
        if not demo_cats:
            self.stdout.write(self.style.SUCCESS("Aucune catégorie « Démo catalogue » trouvée."))
            return

        fallback = (
            Category.objects.filter(
                is_active=True,
                vendor__isnull=True,
                service_provider__isnull=True,
                parent__isnull=True,
            )
            .exclude(name__icontains="Démo catalogue")
            .order_by("id")
            .first()
        )

        for cat in demo_cats:
            count = Product.objects.filter(category=cat).count()
            self.stdout.write(f"  • {cat.name} (id={cat.pk}) — {count} produit(s)")
            if dry:
                continue
            with transaction.atomic():
                if fallback and count:
                    Product.objects.filter(category=cat).update(category=fallback)
                    self.stdout.write(
                        self.style.WARNING(
                            f"    -> produits reaffectes vers « {fallback.name} »"
                        )
                    )
                cat.delete()

        if dry:
            self.stdout.write(self.style.WARNING("Mode dry-run : rien n'a été supprimé."))
        else:
            self.stdout.write(self.style.SUCCESS("Catégories démo retirées du catalogue public."))

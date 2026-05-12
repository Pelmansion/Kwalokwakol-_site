"""
Crée un jeu de données de test complet pour démo / dev.

Usage :
    python manage.py seed_test_data
    python manage.py seed_test_data --reset       # supprime les données de test avant de re-seeder
    python manage.py seed_test_data --password monpwd

Les comptes créés ont tous le mot de passe par défaut "demo1234"
sauf si --password est fourni.

La commande est IDEMPOTENTE : on peut la relancer sans dupliquer.
"""
from __future__ import annotations

import io
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import UserProfile
from catalog.models import Category, Product
from culture.models import (
    ArtistProfile,
    Event,
    MusicGenre,
    Song,
    Ticket,
    TicketCategory,
)
from marketplace.models import ServiceProvider, Vendor
from orders.models import Order, OrderItem, OrderStatusHistory
from reviews.models import Review
from subscriptions.models import Subscription, SubscriptionPlan

User = get_user_model()


# ---------------------------------------------------------------------------
# Génération d'images placeholders (sans dépendance externe)
# ---------------------------------------------------------------------------
def make_placeholder_image(text: str, *, size=(640, 400), bg=(194, 65, 12), fg=(255, 255, 255)) -> ContentFile:
    """Génère un PNG placeholder avec le texte centré (via Pillow)."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text(((size[0] - w) / 2, (size[1] - h) / 2 - 10), text, fill=fg, font=font)
    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f"{slugify(text)}.png")


# Bytes d'un MP3 silencieux minimal valide (1 frame, ~26ms)
# Header MPEG audio frame v1 layer 3, 128kbps, 44100Hz, mono
SILENT_MP3_FRAME = (
    b"\xff\xfb\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
)


def make_silent_mp3(name: str = "silent") -> ContentFile:
    """Petit MP3 silencieux (~1KB) pour tests. Le navigateur reconnaît le format."""
    data = SILENT_MP3_FRAME * 32
    return ContentFile(data, name=f"{slugify(name)}.mp3")


# ---------------------------------------------------------------------------
# Données de référence
# ---------------------------------------------------------------------------
TEST_USERNAMES = {
    "admin",
    "superadmin",
    "client.aya", "client.kouame", "client.fatou", "client.adjoa", "client.ousmane",
    "vendor.kone", "vendor.diallo", "vendor.bamba", "vendor.coulibaly",
    "provider.kouassi", "provider.toure", "provider.yao", "provider.sangare",
}

CITIES = ["Abidjan", "Korhogo", "Bouaké", "Yamoussoukro", "San Pedro", "Daloa", "Man"]
REGIONS = ["Lagunes", "Poro", "Vallée du Bandama", "Belier", "San Pedro", "Haut-Sassandra", "Tonkpi"]


# ---------------------------------------------------------------------------
# Commande
# ---------------------------------------------------------------------------
class Command(BaseCommand):
    help = "Génère un jeu de données de démonstration complet (utilisateurs, produits, abonnements, artistes, concerts, billets...)."

    def add_arguments(self, parser):
        parser.add_argument("--password", default="demo1234",
                            help="Mot de passe commun à tous les comptes de test.")
        parser.add_argument("--reset", action="store_true",
                            help="Supprime d'abord toutes les données de test existantes.")
        parser.add_argument("--purge-orphans", action="store_true",
                            help="Supprime aussi tous les vendeurs/prestataires orphelins (sans owner).")

    def handle(self, *args, **options):
        self.password = options["password"]
        random.seed(42)

        if options["purge_orphans"]:
            self.purge_orphans()

        if options["reset"]:
            self.reset_data()

        with transaction.atomic():
            self.stdout.write(self.style.MIGRATE_HEADING("→ Comptes administrateurs"))
            self.create_admins()

            self.stdout.write(self.style.MIGRATE_HEADING("→ Clients"))
            clients = self.create_clients()

            self.stdout.write(self.style.MIGRATE_HEADING("→ Vendeurs"))
            vendors = self.create_vendors()

            self.stdout.write(self.style.MIGRATE_HEADING("→ Prestataires de services"))
            providers = self.create_providers()

            self.stdout.write(self.style.MIGRATE_HEADING("→ Abonnements"))
            self.create_subscriptions(vendors, providers)

            self.stdout.write(self.style.MIGRATE_HEADING("→ Catégories & Produits"))
            products = self.create_products(vendors, providers)

            self.stdout.write(self.style.MIGRATE_HEADING("→ Commandes & Avis"))
            self.create_orders_and_reviews(clients, products)

            self.stdout.write(self.style.MIGRATE_HEADING("→ Profils artistes"))
            artists = self.activate_artists(vendors, providers)

            self.stdout.write(self.style.MIGRATE_HEADING("→ Catalogue musical"))
            self.create_songs(artists)

            self.stdout.write(self.style.MIGRATE_HEADING("→ Concerts & billetterie"))
            self.create_events(artists, clients)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("✓ Données de test créées avec succès !"))
        self.print_summary()

    # ------------------------------------------------------------------
    # Purge des orphelins (vendeurs/prestataires sans owner)
    # ------------------------------------------------------------------
    def purge_orphans(self):
        self.stdout.write(self.style.WARNING("⚠ Suppression des vendeurs/prestataires orphelins..."))
        v_count, _ = Vendor.objects.filter(owner__isnull=True).delete()
        p_count, _ = ServiceProvider.objects.filter(owner__isnull=True).delete()
        self.stdout.write(f"  {v_count} vendeurs orphelins et {p_count} prestataires orphelins supprimés.")

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------
    def reset_data(self):
        self.stdout.write(self.style.WARNING("⚠ Suppression des données de test..."))

        # 1. Produits, commandes, avis de démo
        Review.objects.filter(comment__startswith="[DEMO]").delete()
        OrderItem.objects.filter(order__full_name__startswith="[DEMO]").delete()
        OrderStatusHistory.objects.filter(order__full_name__startswith="[DEMO]").delete()
        Order.objects.filter(full_name__startswith="[DEMO]").delete()
        Product.objects.filter(name__startswith="[DEMO]").delete()

        # 2. Concerts & billets de démo
        Ticket.objects.filter(event__title__startswith="[DEMO]").delete()
        TicketCategory.objects.filter(event__title__startswith="[DEMO]").delete()
        Event.objects.filter(title__startswith="[DEMO]").delete()

        # 3. Chansons des artistes test (via ArtistProfile.user)
        usernames = list(TEST_USERNAMES - {"admin", "superadmin"})
        Song.objects.filter(artist__user__username__in=usernames).delete()
        ArtistProfile.objects.filter(user__username__in=usernames).delete()

        # 4. Abonnements liés aux vendeurs/prestataires test
        Subscription.objects.filter(vendor__id_number__startswith="CI-VENDOR-").delete()
        Subscription.objects.filter(service_provider__id_number__startswith="CI-PROV-").delete()

        # 5. Vendeurs / prestataires test (y compris orphelins)
        Vendor.objects.filter(id_number__startswith="CI-VENDOR-").delete()
        ServiceProvider.objects.filter(id_number__startswith="CI-PROV-").delete()
        # Filet de sécurité : tout vendeur dont l'email est en @demo.kwalo.local
        Vendor.objects.filter(email__endswith="@demo.kwalo.local").delete()
        ServiceProvider.objects.filter(email__endswith="@demo.kwalo.local").delete()

        # 6. Comptes utilisateurs test (sauf admin/superadmin)
        deleted, _ = User.objects.filter(username__in=usernames).delete()
        self.stdout.write(f"  {deleted} objets liés aux utilisateurs supprimés.")

    # ------------------------------------------------------------------
    # Comptes
    # ------------------------------------------------------------------
    def _make_user(self, username, *, email=None, first="", last="", role=UserProfile.ROLE_CUSTOMER,
                   is_staff=False, is_superuser=False, phone="", city=""):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email or f"{username}@demo.kwalo.local",
                "first_name": first,
                "last_name": last,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        if created:
            user.set_password(self.password)
            user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.role != role or profile.phone != phone or profile.city != city:
            profile.role = role
            profile.phone = phone or profile.phone
            profile.city = city or profile.city
            profile.save()
        return user, created

    def create_admins(self):
        admin, c1 = self._make_user(
            "admin",
            first="Admin", last="Kolê",
            role=UserProfile.ROLE_ADMIN,
            phone="+225 07 00 00 00 01",
        )
        super_admin, c2 = self._make_user(
            "superadmin",
            first="Super", last="Admin",
            role=UserProfile.ROLE_SUPER_ADMIN,
            is_staff=True, is_superuser=True,
            phone="+225 07 00 00 00 02",
        )
        for u, c in [(admin, c1), (super_admin, c2)]:
            self.stdout.write(f"  {'+' if c else '·'} {u.username} ({u.userprofile.get_role_display()})")

    def create_clients(self):
        seed = [
            ("client.aya",       "aya@demo.kwalo.local",      "Aya",    "N'Guessan",  "+225 07 11 11 11 11", "Abidjan"),
            ("client.kouame",    "kouame@demo.kwalo.local",   "Kouamé", "Bahi",       "+225 07 11 11 11 12", "Bouaké"),
            ("client.fatou",     "fatou@demo.kwalo.local",    "Fatou",  "Diabaté",    "+225 07 11 11 11 13", "Korhogo"),
            ("client.adjoa",     "adjoa@demo.kwalo.local",    "Adjoa",  "Konan",      "+225 07 11 11 11 14", "Yamoussoukro"),
            ("client.ousmane",   "ousmane@demo.kwalo.local",  "Ousmane","Cissé",      "+225 07 11 11 11 15", "San Pedro"),
        ]
        clients = []
        for username, email, first, last, phone, city in seed:
            user, created = self._make_user(
                username, email=email, first=first, last=last,
                role=UserProfile.ROLE_CUSTOMER,
                phone=phone, city=city,
            )
            self.stdout.write(f"  {'+' if created else '·'} {username} — {first} {last} ({city})")
            clients.append(user)
        return clients

    def _safe_get_or_create(self, model, *, owner, email, id_number, defaults):
        """Crée ou récupère un Vendor/ServiceProvider en gérant les orphelins.

        Évite les UNIQUE constraint failures sur email / id_number quand un
        ancien enregistrement existe sans owner (ex : suite à un User supprimé
        avec on_delete=SET_NULL).
        """
        instance = model.objects.filter(owner=owner).first()
        if instance:
            return instance, False

        # Orphelin avec même email ou id_number ? On le réattribue.
        instance = model.objects.filter(email=email).first() or \
                   model.objects.filter(id_number=id_number).first()
        if instance:
            instance.owner = owner
            instance.email = email
            instance.id_number = id_number
            for k, v in defaults.items():
                setattr(instance, k, v)
            instance.save()
            return instance, True

        # Création normale
        instance = model.objects.create(
            owner=owner, email=email, id_number=id_number, **defaults
        )
        return instance, True

    def create_vendors(self):
        seed = [
            {
                "username": "vendor.kone",
                "first": "Mariam", "last": "Koné",
                "name": "Boutique Mariam Koné",
                "city": "Abidjan",
                "description": "Vivriers locaux, riz, attiéké, manioc et produits frais en circuit court.",
                "verified": True,
                "offer": Vendor.OFFER_PRODUCT,
            },
            {
                "username": "vendor.diallo",
                "first": "Ibrahima", "last": "Diallo",
                "name": "Diallo Électroménager",
                "city": "Bouaké",
                "description": "Climatiseurs, frigos, ventilateurs, garantie 1 an. Livraison express en zone urbaine.",
                "verified": True,
                "offer": Vendor.OFFER_PRODUCT,
            },
            {
                "username": "vendor.bamba",
                "first": "Aïcha", "last": "Bamba",
                "name": "Aïcha Couture & Style",
                "city": "Korhogo",
                "description": "Pagne tissé senufo, tenues sur mesure, accessoires faits main.",
                "verified": True,
                "offer": Vendor.OFFER_BOTH,
            },
            {
                "username": "vendor.coulibaly",
                "first": "Sékou", "last": "Coulibaly",
                "name": "Coulibaly Hi-Tech",
                "city": "Abidjan",
                "description": "Smartphones, ordinateurs portables, accessoires et SAV.",
                "verified": False,
                "offer": Vendor.OFFER_PRODUCT,
            },
        ]
        vendors = []
        for s in seed:
            user, created = self._make_user(
                s["username"],
                first=s["first"], last=s["last"],
                role=UserProfile.ROLE_CUSTOMER,
                phone=f"+225 07 22 22 22 {len(vendors)+10}",
                city=s["city"],
            )
            vendor, vendor_created = self._safe_get_or_create(
                Vendor,
                owner=user,
                email=user.email,
                id_number=f"CI-VENDOR-{user.pk:04d}",
                defaults={
                    "name": s["name"],
                    "description": s["description"],
                    "phone": user.userprofile.phone,
                    "location": s["city"],
                    "offer_type": s["offer"],
                    "verification_status": (
                        Vendor.STATUS_VERIFIED if s["verified"] else Vendor.STATUS_PENDING
                    ),
                    "verified_at": timezone.now() if s["verified"] else None,
                },
            )
            if vendor_created and not vendor.id_document_front:
                # Documents KYC
                vendor.id_document_front = make_placeholder_image(f"CNI Recto - {s['first']}", bg=(31, 17, 71))
                vendor.id_document_back = make_placeholder_image(f"CNI Verso - {s['first']}", bg=(31, 17, 71))
                vendor.profile_photo = make_placeholder_image(s["first"][0] + s["last"][0], size=(400, 400), bg=(194, 65, 12))
                vendor.save()
            self.stdout.write(f"  {'+' if vendor_created else '·'} {s['name']} ({'✓' if s['verified'] else '⏳'})")
            vendors.append(vendor)
        return vendors

    def create_providers(self):
        seed = [
            {
                "username": "provider.kouassi", "first": "Yao", "last": "Kouassi",
                "name": "Kouassi Plomberie Express", "city": "Abidjan",
                "description": "Plombier qualifié 12 ans d'expérience. Dépannage 24/7, devis gratuit.",
                "verified": True,
            },
            {
                "username": "provider.toure", "first": "Aminata", "last": "Touré",
                "name": "Salon Aminata Beauté", "city": "Bouaké",
                "description": "Coiffure, manucure, soins du visage. Sur rdv ou à domicile.",
                "verified": True,
            },
            {
                "username": "provider.yao", "first": "Yannick", "last": "Yao",
                "name": "Yao Digital Studio", "city": "Abidjan",
                "description": "Création de sites web, logos, gestion réseaux sociaux. Tarifs étudiants.",
                "verified": True,
            },
            {
                "username": "provider.sangare", "first": "Drissa", "last": "Sangaré",
                "name": "Drissa Bâtiment & Travaux", "city": "Korhogo",
                "description": "Maçonnerie, peinture, carrelage. Équipe de 6 ouvriers.",
                "verified": False,
            },
        ]
        providers = []
        for i, s in enumerate(seed):
            user, _ = self._make_user(
                s["username"],
                first=s["first"], last=s["last"],
                phone=f"+225 07 33 33 33 {i+10}",
                city=s["city"],
            )
            provider, created = self._safe_get_or_create(
                ServiceProvider,
                owner=user,
                email=user.email,
                id_number=f"CI-PROV-{user.pk:04d}",
                defaults={
                    "name": s["name"],
                    "description": s["description"],
                    "phone": user.userprofile.phone,
                    "location": s["city"],
                    "verification_status": (
                        ServiceProvider.STATUS_VERIFIED if s["verified"] else ServiceProvider.STATUS_PENDING
                    ),
                    "verified_at": timezone.now() if s["verified"] else None,
                    "display_services_as_provider": True,
                },
            )
            if created and not provider.id_document_front:
                provider.id_document_front = make_placeholder_image(f"CNI Recto - {s['first']}", bg=(31, 17, 71))
                provider.id_document_back = make_placeholder_image(f"CNI Verso - {s['first']}", bg=(31, 17, 71))
                provider.profile_photo = make_placeholder_image(s["first"][0] + s["last"][0], size=(400, 400), bg=(99, 102, 241))
                provider.save()
            self.stdout.write(f"  {'+' if created else '·'} {s['name']} ({'✓' if s['verified'] else '⏳'})")
            providers.append(provider)
        return providers

    # ------------------------------------------------------------------
    # Abonnements
    # ------------------------------------------------------------------
    def create_subscriptions(self, vendors, providers):
        plans = list(SubscriptionPlan.objects.filter(is_active=True).order_by("monthly_amount"))
        if not plans:
            self.stdout.write("  ⚠ Aucun plan d'abonnement trouvé. Skip.")
            return

        # Distribution : 3 actifs, 1 pending pour vendeurs et prestataires
        configs_v = [
            (Subscription.STATUS_ACTIVE, plans[0], 0),    # Starter actif
            (Subscription.STATUS_ACTIVE, plans[1], 0),    # Pro actif
            (Subscription.STATUS_ACTIVE, plans[-1], 0),   # Premium actif
            (Subscription.STATUS_PENDING, plans[0], 1),   # Pending (paiement non fait)
        ]
        for vendor, (status, plan, _) in zip(vendors, configs_v):
            sub, created = Subscription.objects.get_or_create(
                vendor=vendor,
                defaults={
                    "plan": plan,
                    "monthly_amount": plan.monthly_amount,
                    "status": Subscription.STATUS_PENDING,
                },
            )
            if status == Subscription.STATUS_ACTIVE and not sub.is_active_now():
                sub.activate_period(days=30)
            self.stdout.write(f"  {'+' if created else '·'} {vendor.name} → {plan.name} ({sub.status})")

        configs_p = [
            (Subscription.STATUS_ACTIVE, plans[1], 0),
            (Subscription.STATUS_ACTIVE, plans[-1], 0),
            (Subscription.STATUS_ACTIVE, plans[0], 0),
            (Subscription.STATUS_PENDING, plans[0], 1),
        ]
        for provider, (status, plan, _) in zip(providers, configs_p):
            sub, created = Subscription.objects.get_or_create(
                service_provider=provider,
                defaults={
                    "plan": plan,
                    "monthly_amount": plan.monthly_amount,
                    "status": Subscription.STATUS_PENDING,
                },
            )
            if status == Subscription.STATUS_ACTIVE and not sub.is_active_now():
                sub.activate_period(days=30)
            self.stdout.write(f"  {'+' if created else '·'} {provider.name} → {plan.name} ({sub.status})")

    # ------------------------------------------------------------------
    # Produits
    # ------------------------------------------------------------------
    def create_products(self, vendors, providers):
        cats = {
            c.name.lower(): c
            for c in Category.objects.filter(
                vendor__isnull=True, service_provider__isnull=True
            )
        }

        def cat(*names):
            for n in names:
                for k, v in cats.items():
                    if n.lower() in k:
                        return v
            return next(iter(cats.values())) if cats else None

        seed = [
            # Vendor 0 — Boutique Mariam Koné (alimentation)
            (vendors[0], cat("alimentation", "vivriers"), "Riz parfumé local 25kg",      9500,  10500, 50, "https://images.unsplash.com/photo-1604908176997-431f9b9b6c45?w=600"),
            (vendors[0], cat("alimentation", "vivriers"), "Attiéké frais 1kg",            500,  None,  100, "https://images.unsplash.com/photo-1505253758473-96b7015fcd40?w=600"),
            (vendors[0], cat("alimentation"),             "Huile de palme rouge 5L",     6000,  6500,   30, "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?w=600"),
            (vendors[0], cat("alimentation"),             "Poisson fumé bonga 1kg",      3500,  None,   25, "https://images.unsplash.com/photo-1584270354949-c26b0d5b0a82?w=600"),
            # Vendor 1 — Diallo Électroménager
            (vendors[1], cat("electromenager"),           "Climatiseur split 1.5 CV",  225000, 250000,  8, "https://images.unsplash.com/photo-1631545806609-7a2d3b6f9c80?w=600"),
            (vendors[1], cat("electromenager"),           "Frigo 200L Hisense",         180000, None,   12, "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=600"),
            (vendors[1], cat("electromenager"),           "Ventilateur sur pied",        18000, 22000,  35, "https://images.unsplash.com/photo-1565374395542-0ce18882c857?w=600"),
            # Vendor 2 — Aïcha Couture
            (vendors[2], cat("boutiques", "production"),  "Pagne tissé senufo (6 yards)", 28000, None,  20, "https://images.unsplash.com/photo-1584472331423-c95c1a6d2a08?w=600"),
            (vendors[2], cat("boutiques", "production"),  "Tenue homme bazin brodé",      45000, 55000, 10, "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=600"),
            (vendors[2], cat("boutiques"),                "Foulard wax assorti",           4500, None,  50, "https://images.unsplash.com/photo-1551232864-3f0890e580d9?w=600"),
            # Vendor 3 — Coulibaly Hi-Tech
            (vendors[3], cat("numerique", "boutiques"),   "Smartphone Tecno Spark 10",   95000, 110000,15, "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600"),
            (vendors[3], cat("numerique", "boutiques"),   "Écouteurs Bluetooth Realme",   8500, 12000, 30, "https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?w=600"),
        ]
        services = [
            (providers[0], cat("services", "batiment"), "Dépannage plomberie urgent",     5000, "Intervention sous 1h dans Abidjan."),
            (providers[0], cat("services", "batiment"), "Installation salle de bain",   150000, "Pose complète : douche, lavabo, WC."),
            (providers[1], cat("services"),             "Coiffure tresses africaines",   12000, "Tresses, défrisage, coloration."),
            (providers[1], cat("services"),             "Manucure + pédicure",            6000, "Soin complet 1h30."),
            (providers[2], cat("numerique", "services"), "Création site vitrine",       250000, "Site responsive 5 pages, 1 mois de maintenance."),
            (providers[2], cat("numerique", "services"), "Logo professionnel",            35000, "3 propositions, fichiers source inclus."),
            (providers[3], cat("batiment", "services"), "Peinture maison (au m²)",        2500, "Peinture intérieure 2 couches, fournitures comprises."),
        ]

        products = []
        for vendor, category, name, price, old_price, stock, img in seed:
            product, created = Product.objects.get_or_create(
                name=f"[DEMO] {name}",
                vendor=vendor,
                defaults={
                    "category": category,
                    "description": f"Article de qualité, vendu par {vendor.name}.",
                    "price": Decimal(str(price)),
                    "old_price": Decimal(str(old_price)) if old_price else None,
                    "stock": stock,
                    "image_url": img,
                    "kind": Product.PRODUCT,
                    "location": vendor.location,
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(f"  + {name} ({price} FCFA) — {vendor.name}")
            products.append(product)

        for provider, category, name, price, desc in services:
            product, created = Product.objects.get_or_create(
                name=f"[DEMO] {name}",
                service_provider=provider,
                defaults={
                    "category": category,
                    "description": desc,
                    "price": Decimal(str(price)),
                    "stock": 9999,
                    "kind": Product.SERVICE,
                    "location": provider.location,
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(f"  + [SERVICE] {name} ({price} FCFA) — {provider.name}")
            products.append(product)
        return products

    # ------------------------------------------------------------------
    # Commandes & Avis
    # ------------------------------------------------------------------
    def create_orders_and_reviews(self, clients, products):
        product_only = [p for p in products if p.kind == Product.PRODUCT]
        if not product_only:
            return

        # 8 commandes avec différents statuts
        statuses = [
            (Order.STATUS_DONE, Order.PAYMENT_SUCCESS),
            (Order.STATUS_DONE, Order.PAYMENT_SUCCESS),
            (Order.STATUS_SHIPPED, Order.PAYMENT_SUCCESS),
            (Order.STATUS_PAID, Order.PAYMENT_SUCCESS),
            (Order.STATUS_PAID, Order.PAYMENT_SUCCESS),
            (Order.STATUS_PENDING, Order.PAYMENT_PENDING),
            (Order.STATUS_PENDING, Order.PAYMENT_PENDING),
            (Order.STATUS_CANCELLED, Order.PAYMENT_FAILED),
        ]

        if Order.objects.filter(full_name__startswith="[DEMO]").exists():
            self.stdout.write("  · Commandes déjà existantes, skip.")
        else:
            for client, (status, payment_status) in zip(clients * 2, statuses):
                items = random.sample(product_only, k=min(2, len(product_only)))
                total = sum(p.price for p in items) + Decimal("1500")
                order = Order.objects.create(
                    user=client,
                    full_name=f"[DEMO] {client.first_name} {client.last_name}",
                    phone=client.userprofile.phone or "+225 07 00 00 00 00",
                    email=client.email,
                    address=f"Rue {random.randint(10, 99)}, quartier {random.choice(['Cocody', 'Yopougon', 'Plateau', 'Treichville'])}",
                    city=client.userprofile.city or "Abidjan",
                    delivery_option=Order.DELIVERY_STANDARD,
                    delivery_fee=Decimal("1500"),
                    status=status,
                    payment_status=payment_status,
                    payment_method=random.choice([Order.METHOD_MOBILE, Order.METHOD_CARD]),
                    total_amount=total,
                    tracking_code=f"KW{random.randint(100000, 999999)}",
                )
                for product in items:
                    OrderItem.objects.create(
                        order=order, product=product,
                        quantity=random.randint(1, 3),
                        unit_price=product.price,
                    )
                OrderStatusHistory.objects.create(
                    order=order, status=status,
                    note=f"Statut initial : {order.get_status_display()}",
                )
            self.stdout.write(f"  + 8 commandes créées (statuts variés)")

        # Reviews sur les produits livrés
        if not Review.objects.filter(comment__startswith="[DEMO]").exists():
            sample_reviews = [
                (5, "[DEMO] Excellent produit, conforme à la description !"),
                (5, "[DEMO] Livraison rapide, qualité top."),
                (4, "[DEMO] Très bon rapport qualité-prix, à recommander."),
                (4, "[DEMO] Bon produit, l'emballage pourrait être amélioré."),
                (3, "[DEMO] Correct, sans plus."),
                (5, "[DEMO] Parfait, je recommande Kolê !"),
            ]
            for product, (rating, comment) in zip(product_only[:6], sample_reviews):
                Review.objects.create(
                    product=product,
                    user=random.choice(clients),
                    rating=rating,
                    comment=comment,
                )
            self.stdout.write(f"  + {len(sample_reviews)} avis ajoutés")

    # ------------------------------------------------------------------
    # Profils artistes
    # ------------------------------------------------------------------
    def activate_artists(self, vendors, providers):
        # Active 3 artistes : 2 vendeurs + 1 prestataire
        candidates = [
            # (owner_user, stage_name, region, city, genre_name, bio, social)
            (vendors[2].owner, "Aïcha Wakolê", "Poro", "Korhogo", "Coupé-décalé",
             "Chanteuse et créatrice de mode, Aïcha mêle tradition senufo et sons modernes.",
             {"facebook": "https://facebook.com/aichawakole", "instagram": "https://instagram.com/aichawakole"}),
            (vendors[1].owner, "DJ Diallo", "Vallée du Bandama", "Bouaké", "Électro / DJ",
             "Producteur de beats afro-électro, résident dans les meilleurs clubs d'Abidjan.",
             {"youtube": "https://youtube.com/@djdiallo", "spotify": "https://open.spotify.com/artist/demo"}),
            (providers[2].owner, "Yannick Soul", "Lagunes", "Abidjan", "R&B / Soul",
             "Auteur-compositeur, voix soul et textes engagés sur la jeunesse africaine.",
             {"instagram": "https://instagram.com/yannicksoul", "tiktok": "https://tiktok.com/@yannicksoul"}),
        ]
        artists = []
        for user, stage_name, region, city, genre_name, bio, socials in candidates:
            genre = MusicGenre.objects.filter(name__iexact=genre_name).first() or MusicGenre.objects.first()
            artist, created = ArtistProfile.objects.get_or_create(
                user=user,
                defaults={
                    "stage_name": stage_name,
                    "bio": bio,
                    "primary_genre": genre,
                    "region": region,
                    "city": city,
                    "phone": user.userprofile.phone,
                    "whatsapp": user.userprofile.phone,
                    "email": user.email,
                    "is_verified": True,
                    "is_featured": True,
                    "is_active": True,
                    **socials,
                },
            )
            if created:
                artist.portrait = make_placeholder_image(stage_name[:2].upper(), size=(400, 400), bg=(31, 17, 71))
                artist.cover_photo = make_placeholder_image(stage_name, size=(1200, 600), bg=(194, 65, 12))
                artist.save()
            self.stdout.write(f"  {'+' if created else '·'} 🎤 {stage_name} — {genre_name} ({city})")
            artists.append(artist)
        return artists

    # ------------------------------------------------------------------
    # Chansons
    # ------------------------------------------------------------------
    def create_songs(self, artists):
        # Chaque artiste : 3-4 chansons avec mix gratuit/payant
        catalog = {
            "Aïcha Wakolê": [
                ("Yelo Mama",       "Coupé-décalé",       True,  0,    True),
                ("Korhogo Vibes",   "Coupé-décalé",       False, 1500, True),
                ("Dimanche au village", "Variété africaine", True,  0,    True),
            ],
            "DJ Diallo": [
                ("Bouaké by Night",   "Électro / DJ", True,  0,    True),
                ("Afro House Mix #1", "Électro / DJ", False, 2000, True),
                ("Dancefloor 225",    "Coupé-décalé", False, 1000, True),
                ("Sunrise Set",       "Électro / DJ", True,  0,    False),  # streaming désactivé
            ],
            "Yannick Soul": [
                ("Génération 225",   "R&B / Soul",   False, 2500, True),
                ("Mama Africa",      "R&B / Soul",   True,  0,    True),
                ("Lettres à Aïcha",  "R&B / Soul",   False, 1500, True),
            ],
        }
        for artist in artists:
            for title, genre_name, is_free, price, allow_stream in catalog.get(artist.stage_name, []):
                genre = MusicGenre.objects.filter(name__iexact=genre_name).first()
                song, created = Song.objects.get_or_create(
                    artist=artist, title=title,
                    defaults={
                        "genre": genre,
                        "description": f"Extrait de l'univers musical de {artist.stage_name}.",
                        "release_date": timezone.now().date() - timedelta(days=random.randint(30, 365)),
                        "duration_seconds": random.randint(180, 240),
                        "pricing": Song.PRICING_FREE if is_free else Song.PRICING_PAID,
                        "price_fcfa": Decimal(str(price)),
                        "allow_streaming": allow_stream,
                        "is_published": True,
                        "is_featured": random.random() < 0.3,
                        "play_count": random.randint(50, 5000),
                        "download_count": random.randint(5, 500),
                    },
                )
                if created:
                    song.cover_image = make_placeholder_image(title[:8], size=(500, 500), bg=(99, 102, 241))
                    song.audio_file.save(f"{slugify(title)}.mp3", make_silent_mp3(title), save=False)
                    song.save()
                    self.stdout.write(f"  + 🎵 {title} ({'GRATUIT' if is_free else f'{price} FCFA'}) — {artist.stage_name}")

    # ------------------------------------------------------------------
    # Concerts & billets
    # ------------------------------------------------------------------
    def create_events(self, artists, clients):
        if not artists:
            return

        now = timezone.now()
        events_data = [
            {
                "headliner": artists[0],
                "title": "[DEMO] Korhogo Live Festival 2026",
                "description": "Le rendez-vous incontournable des artistes du Nord. Aïcha Wakolê en tête d'affiche, supportée par les talents émergents de la région Poro.",
                "starts_at": now + timedelta(days=30, hours=20),
                "venue_name": "Stade Municipal de Korhogo",
                "city": "Korhogo",
                "region": "Poro",
                "categories": [
                    ("Standard", 5000, 500, "#64748b", "Accès parterre, ambiance garantie."),
                    ("VIP", 15000, 100, "#C2410C", "Accès loge VIP, boissons offertes, parking dédié."),
                    ("Carré Or", 30000, 30, "#fbbf24", "Premier rang, after-show avec les artistes, photo souvenir."),
                ],
            },
            {
                "headliner": artists[1],
                "title": "[DEMO] Bouaké Electro Night",
                "description": "DJ Diallo aux platines pour une nuit électro-afro inoubliable, avec écran géant et lasers.",
                "starts_at": now + timedelta(days=15, hours=22),
                "venue_name": "Espace Diallo Lounge",
                "city": "Bouaké",
                "region": "Vallée du Bandama",
                "categories": [
                    ("Standard", 3000, 300, "#64748b", "Entrée + 1 boisson offerte."),
                    ("VIP", 10000, 50, "#C2410C", "Espace lounge, open bar 2h, parking sécurisé."),
                ],
            },
            {
                "headliner": artists[2],
                "title": "[DEMO] Concert Yannick Soul - Génération 225",
                "description": "Concert intimiste acoustique avec Yannick Soul. Ambiance feutrée, textes engagés, voix soul.",
                "starts_at": now + timedelta(days=45, hours=20),
                "venue_name": "Théâtre Beausejour",
                "city": "Abidjan",
                "region": "Lagunes",
                "categories": [
                    ("Standard", 7500, 200, "#64748b", "Place assise."),
                    ("Premium", 20000, 50, "#C2410C", "1ère catégorie, meet & greet inclus."),
                ],
            },
            {
                "headliner": artists[0],
                "title": "[DEMO] Kolê Culture Festival - Édition Pilote",
                "description": "Festival inaugural de Kolê Culture : 6h de musique avec tous les artistes de la plateforme. Buvette, food trucks, ambiance familiale.",
                "starts_at": now - timedelta(days=20),  # Événement passé pour démo
                "venue_name": "Place Ficgayo",
                "city": "Abidjan",
                "region": "Lagunes",
                "categories": [
                    ("Standard", 2000, 1000, "#64748b", "Entrée libre festival."),
                ],
            },
        ]

        for ev in events_data:
            event, created = Event.objects.get_or_create(
                title=ev["title"],
                defaults={
                    "headlining_artist": ev["headliner"],
                    "organizer": ev["headliner"].user,
                    "description": ev["description"],
                    "starts_at": ev["starts_at"],
                    "ends_at": ev["starts_at"] + timedelta(hours=4),
                    "venue_name": ev["venue_name"],
                    "city": ev["city"],
                    "region": ev["region"],
                    "address": f"Avenue {random.choice(['de la République', 'des Artistes', 'Houphouët-Boigny'])}",
                    "status": Event.STATUS_PUBLISHED,
                    "is_published": True,
                    "is_featured": True,
                },
            )
            if created:
                event.poster = make_placeholder_image(ev["title"][7:25], size=(1200, 700), bg=(31, 17, 71))
                event.save()

                for i, (cat_name, price, qty, color, desc) in enumerate(ev["categories"]):
                    TicketCategory.objects.create(
                        event=event,
                        name=cat_name,
                        description=desc,
                        price_fcfa=Decimal(str(price)),
                        quantity_total=qty,
                        color=color,
                        display_order=i,
                    )
                self.stdout.write(f"  + 🎫 {ev['title']} ({len(ev['categories'])} catégories)")

                # Quelques billets vendus pour les événements futurs
                if event.starts_at > now:
                    self._create_sample_tickets(event, clients)

    def _create_sample_tickets(self, event, clients):
        """Crée 3-8 billets vendus pour donner un peu d'historique."""
        n_tickets = random.randint(3, 8)
        categories = list(event.ticket_categories.all())
        for _ in range(n_tickets):
            cat = random.choice(categories)
            client = random.choice(clients)
            ticket = Ticket.objects.create(
                event=event,
                category=cat,
                buyer=client,
                buyer_name=f"{client.first_name} {client.last_name}",
                buyer_email=client.email,
                buyer_phone=client.userprofile.phone or "+225 07 00 00 00 00",
                amount_fcfa=cat.price_fcfa,
                status=Ticket.STATUS_VALID,
                payment_method="sandbox",
                paid_at=timezone.now() - timedelta(days=random.randint(1, 5)),
            )
            TicketCategory.objects.filter(pk=cat.pk).update(
                quantity_sold=models_F("quantity_sold") + 1
            )

    # ------------------------------------------------------------------
    # Récap
    # ------------------------------------------------------------------
    def print_summary(self):
        from django.db.models import Count
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("═══ RÉCAPITULATIF ═══"))
        self.stdout.write(f"  • Utilisateurs    : {User.objects.count()}")
        self.stdout.write(f"  • Vendeurs        : {Vendor.objects.count()}")
        self.stdout.write(f"  • Prestataires    : {ServiceProvider.objects.count()}")
        self.stdout.write(f"  • Abonnements actifs : {Subscription.objects.filter(status='active').count()}")
        self.stdout.write(f"  • Produits        : {Product.objects.filter(kind=Product.PRODUCT).count()}")
        self.stdout.write(f"  • Services        : {Product.objects.filter(kind=Product.SERVICE).count()}")
        self.stdout.write(f"  • Commandes       : {Order.objects.count()}")
        self.stdout.write(f"  • Avis            : {Review.objects.count()}")
        self.stdout.write(f"  • Artistes        : {ArtistProfile.objects.count()}")
        self.stdout.write(f"  • Chansons        : {Song.objects.count()}")
        self.stdout.write(f"  • Concerts        : {Event.objects.count()}")
        self.stdout.write(f"  • Billets         : {Ticket.objects.count()}")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("═══ COMPTES DE TEST (mot de passe : %s) ═══" % self.password))
        self.stdout.write("")
        self.stdout.write("  ADMINS")
        self.stdout.write("    superadmin / %s    (super-admin Django)" % self.password)
        self.stdout.write("    admin      / %s    (admin plateforme)" % self.password)
        self.stdout.write("")
        self.stdout.write("  CLIENTS")
        for u in User.objects.filter(username__startswith="client.").order_by("username"):
            self.stdout.write(f"    {u.username:<20} / {self.password}    ({u.first_name} {u.last_name})")
        self.stdout.write("")
        self.stdout.write("  VENDEURS")
        for u in User.objects.filter(username__startswith="vendor.").order_by("username"):
            self.stdout.write(f"    {u.username:<20} / {self.password}    ({u.first_name} {u.last_name})")
        self.stdout.write("")
        self.stdout.write("  PRESTATAIRES")
        for u in User.objects.filter(username__startswith="provider.").order_by("username"):
            self.stdout.write(f"    {u.username:<20} / {self.password}    ({u.first_name} {u.last_name})")
        self.stdout.write("")
        artist_users = list(User.objects.filter(artist_profile__isnull=False))
        if artist_users:
            self.stdout.write("  ARTISTES (espace Kolê Culture activé)")
            for u in artist_users:
                self.stdout.write(f"    🎤 {u.username:<17} / {self.password}    ({u.artist_profile.stage_name})")


# Petit helper pour utiliser F() dans la création de billets sans import circulaire
from django.db.models import F as models_F  # noqa: E402

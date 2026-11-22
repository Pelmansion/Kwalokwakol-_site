"""Données de démonstration Dan Prestige Magazine."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from catalog.models import Category, Product
from magazine.models import (
    Article,
    MagazineIssue,
    MagazineSubscriptionPlan,
    Partner,
    Personality,
    Portrait,
    TeamMember,
    Video,
)


class Command(BaseCommand):
    help = "Crée des contenus de démonstration pour Dan Prestige Magazine."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Dan Prestige Magazine (demo)"))
        self._team()
        self._partners()
        self._articles()
        self._videos()
        self._portraits()
        self._personalities()
        self._plans()
        self._issues()
        self.stdout.write(self.style.SUCCESS("Magazine seede."))

    def _team(self):
        roles = [
            ("Directeur de publication", "Supervision éditoriale et stratégique."),
            ("Rédacteur en chef", "Ligne éditoriale et validation des contenus."),
            ("Secrétaire de rédaction", "Coordination des dossiers et planning."),
            ("Responsable communication et marketing", "Visibilité et campagnes."),
            ("Responsable des relations avec les personnalités", "Partenariats humains et consentements."),
            ("Journalistes et correspondants régionaux", "Couverture Ouest montagneux."),
            ("Correspondants de la diaspora", "Relais Europe, Amérique, Afrique."),
            ("Photographes et vidéastes", "Image et formats audiovisuels."),
            ("Responsable commercial et partenariats", "Publicité et sponsoring."),
        ]
        for i, (role, bio) in enumerate(roles):
            TeamMember.objects.update_or_create(
                role=role,
                defaults={
                    "name": f"Équipe {role.split()[0]}",
                    "bio": bio,
                    "display_order": i,
                    "is_active": True,
                },
            )
        self.stdout.write(f"  Équipe : {TeamMember.objects.count()}")

    def _articles(self):
        data = [
            ("Les bâtisseurs de Man", "reportage", "Man", False, "Un reportage sur les entrepreneurs qui transforment la ville."),
            ("Interview : une voix de la diaspora", "interview", "Abidjan", False, "Parcours d'une cadre Dan revenue investir au pays."),
            ("Portrait d'un enseignant engagé", "portrait", "Biankouma", False, "Transmettre le savoir dans les montagnes de l'Ouest."),
            ("Édition spéciale tourisme", "actu", "Touba", True, "Contenu sponsorisé sur le potentiel touristique."),
        ]
        sponsor = Partner.objects.filter(is_sponsor=True).first()
        for title, cat, loc, sponsored, excerpt in data:
            Article.objects.update_or_create(
                slug=slugify(title),
                defaults={
                    "title": title,
                    "category": cat,
                    "locality": loc,
                    "is_sponsored": sponsored,
                    "sponsor": sponsor if sponsored else None,
                    "excerpt": excerpt,
                    "body": excerpt + "\n\n" + ("Lorem ipsum editorial Dan Prestige. " * 12),
                    "author_name": "Rédaction DPM",
                    "is_published": True,
                    "is_featured": not sponsored,
                    "is_demo": True,
                    "published_at": timezone.now() - timedelta(days=len(title)),
                },
            )
        self.stdout.write(f"  Articles : {Article.objects.count()}")

    def _videos(self):
        data = [
            ("Grand entretien — cadres Dan", "interview", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 1240),
            ("Reportage : marchés de l'Ouest", "reportage", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 860),
            ("Émission spéciale diaspora", "emission", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 2100),
        ]
        for title, kind, url, duration in data:
            Video.objects.update_or_create(
                slug=slugify(title),
                defaults={
                    "title": title,
                    "kind": kind,
                    "video_url": url,
                    "duration_seconds": duration,
                    "description": "Vidéo de démonstration Dan Prestige Magazine.",
                    "locality": "Côte d'Ivoire",
                    "is_published": True,
                    "is_featured": True,
                    "is_demo": True,
                },
            )
        self.stdout.write(f"  Vidéos : {Video.objects.count()}")

    def _portraits(self):
        # Portraits sans fichier image réel : on skip image obligatoire en créant via raw si possible
        # ImageField required — on utilise un placeholder path only if we generate; skip if no image.
        # Better: make portraits only when we can use empty - model requires image.
        # We'll create portraits without saving image by temporarily allowing blank - already required.
        # For seed, create articles only; portraits need files. Skip file-required portraits in seed
        # OR use ContentFile placeholder like seed_test_data.
        from accounts.management.commands.seed_test_data import make_placeholder_image

        subjects = [
            ("Aya Goba", "Man"),
            ("Kouamé Blé", "Danané"),
            ("Fatou Guéi", "Biankouma"),
        ]
        for name, loc in subjects:
            slug = slugify(f"portrait-{name}")
            obj, created = Portrait.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": f"Portrait — {name}",
                    "subject_name": name,
                    "locality": loc,
                    "caption": f"Portrait de démonstration : {name}.",
                    "photographer": "Studio DPM",
                    "is_published": True,
                    "is_featured": True,
                    "is_demo": True,
                },
            )
            if not obj.image:
                obj.image = make_placeholder_image(name, size=(600, 600), bg=(44, 33, 24))
                obj.save()
        self.stdout.write(f"  Portraits : {Portrait.objects.count()}")

    def _personalities(self):
        from accounts.management.commands.seed_test_data import make_placeholder_image

        people = [
            ("Aya", "Goba", "Entrepreneure", "Man", True),
            ("Séry", "Blé", "Enseignant-chercheur", "Biankouma", True),
            ("Mariame", "Touré", "Artiste", "Danané", True),
            ("Jean", "Demo", "Sans consentement", "Man", False),
        ]
        for first, last, prof, loc, consent in people:
            obj, _ = Personality.objects.update_or_create(
                slug=slugify(f"{first}-{last}"),
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "profession": prof,
                    "locality": loc,
                    "region": "Montagnes",
                    "bio": f"Parcours de démonstration de {first} {last}.",
                    "achievements": "Engagement communautaire et excellence professionnelle.",
                    "consent_validated": consent,
                    "is_featured": consent,
                    "is_demo": True,
                },
            )
            if not obj.photo:
                obj.photo = make_placeholder_image(f"{first[0]}{last[0]}", size=(400, 400), bg=(194, 65, 12))
                obj.save()
        self.stdout.write(f"  Personnalités : {Personality.objects.filter(consent_validated=True).count()} visibles")

    def _plans(self):
        MagazineSubscriptionPlan.objects.update_or_create(
            slug="mensuel",
            defaults={
                "name": "Abonnement mensuel",
                "period": MagazineSubscriptionPlan.PERIOD_MONTHLY,
                "price_fcfa": Decimal("3000"),
                "tagline": "Chaque nouveau numéro + accès web",
                "features": "Dernier numéro numérique\nAccès articles premium\nNewsletter",
                "is_active": True,
                "is_featured": False,
                "display_order": 1,
            },
        )
        MagazineSubscriptionPlan.objects.update_or_create(
            slug="annuel",
            defaults={
                "name": "Abonnement annuel",
                "period": MagazineSubscriptionPlan.PERIOD_YEARLY,
                "price_fcfa": Decimal("30000"),
                "tagline": "12 mois — 2 mois offerts",
                "features": "Tous les numéros de l'année\nAccès archives\nInvitations événements\nBadge lecteur",
                "is_active": True,
                "is_featured": True,
                "display_order": 2,
            },
        )
        self.stdout.write(f"  Formules : {MagazineSubscriptionPlan.objects.count()}")

    def _issues(self):
        from accounts.management.commands.seed_test_data import make_placeholder_image

        cat, _ = Category.objects.get_or_create(
            name="Dan Prestige Magazine",
            defaults={
                "slug": "dan-prestige-magazine",
                "is_active": True,
            },
        )
        # Ensure slug if created differently
        if not cat.slug:
            cat.slug = "dan-prestige-magazine"
            cat.save(update_fields=["slug"])

        issues_data = [
            (1, "Lancement — Voix et talents Dan", True, False, Decimal("2500")),
            (2, "Diaspora & investissements", False, False, Decimal("2500")),
            (3, "Édition spéciale Montagnes", False, True, Decimal("3500")),
        ]
        for number, title, latest, special, price in issues_data:
            product, _ = Product.objects.update_or_create(
                slug=f"dan-prestige-n{number}",
                defaults={
                    "name": f"Dan Prestige Magazine N°{number}",
                    "description": title,
                    "price": price,
                    "stock": 100,
                    "is_active": True,
                    "category": cat,
                },
            )
            issue, _ = MagazineIssue.objects.update_or_create(
                number=number,
                defaults={
                    "title": title,
                    "summary": f"Sommaire du numéro {number} : {title}.",
                    "published_at": date.today() - timedelta(days=30 * (3 - number)),
                    "price_fcfa": price,
                    "is_latest": latest,
                    "is_special": special,
                    "is_published": True,
                    "product": product,
                },
            )
            if not issue.cover_image:
                issue.cover_image = make_placeholder_image(f"N{number}", size=(600, 800), bg=(26, 21, 16))
                issue.save()
        self.stdout.write(f"  Numéros : {MagazineIssue.objects.count()}")

    def _partners(self):
        for i, name in enumerate(["Mutuelle Dan Solidarité", "Association Développement Ouest", "Sponsor Démo CI"]):
            Partner.objects.update_or_create(
                name=name,
                defaults={
                    "description": "Partenaire de démonstration.",
                    "is_sponsor": i == 2,
                    "is_demo": True,
                    "is_active": True,
                    "display_order": i,
                },
            )
        self.stdout.write(f"  Partenaires : {Partner.objects.count()}")

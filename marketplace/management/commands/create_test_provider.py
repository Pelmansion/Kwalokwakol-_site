"""
Commande pour créer un prestataire de test avec toutes les données nécessaires.
Usage: python manage.py create_test_provider
"""
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image
import io

from marketplace.models import ServiceProvider


class Command(BaseCommand):
    help = "Crée un prestataire de test avec toutes les données nécessaires (email, numéro d'identité, documents)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default="prestataire_test",
            help="Nom d'utilisateur pour le compte prestataire (défaut: prestataire_test).",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="prestataire.test@example.com",
            help="Email unique du prestataire (défaut: prestataire.test@example.com).",
        )
        parser.add_argument(
            "--id-number",
            type=str,
            default="CI-TEST-001",
            help="Numéro d'identité unique (défaut: CI-TEST-001).",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="prestataire123",
            help="Mot de passe pour le compte (défaut: prestataire123).",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]
        email = options["email"]
        id_number = options["id_number"]
        password = options["password"]

        # Créer ou récupérer l'utilisateur
        user, user_created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": "Prestataire",
                "last_name": "Test",
            },
        )
        if user_created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Utilisateur créé: {username}"))
        else:
            self.stdout.write(f"Utilisateur existe déjà: {username}")
            # Mettre à jour l'email si nécessaire
            if user.email != email:
                user.email = email
                user.save()

        # Créer des images de test pour les documents d'identité
        def create_test_image(filename="test_id.png"):
            """Crée une image PNG simple pour les tests."""
            img = Image.new("RGB", (800, 600), color="white")
            # Ajouter un texte simple (nécessite PIL avec support texte ou on peut juste créer une image vide)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return ContentFile(buffer.getvalue(), name=filename)

        # Vérifier si un prestataire existe déjà avec cet owner
        existing_by_owner = ServiceProvider.objects.filter(owner=user).first()
        existing_by_email = ServiceProvider.objects.filter(email=email).exclude(owner=user).first()
        existing_by_id = ServiceProvider.objects.filter(id_number=id_number).exclude(owner=user).first()

        if existing_by_owner:
            self.stdout.write(
                self.style.WARNING(
                    f"Un prestataire existe déjà pour cet utilisateur. Mise à jour de l'existant."
                )
            )
            provider = existing_by_owner
            # Mettre à jour les champs requis
            provider.email = email
            provider.id_number = id_number
            provider.name = "Prestataire de Services Test"
            provider.phone = "+2250102030405"
            provider.location = "Plateau - Abidjan"
            provider.description = "Prestataire de test pour les services numériques et artisanaux."
            provider.services_overview = "Création de sites web, gestion de réseaux sociaux, design graphique, et services artisanaux."
            provider.portfolio_url = "https://example.com/portfolio"
            provider.is_active = True
            provider.verification_status = ServiceProvider.STATUS_VERIFIED
            provider.verified_at = timezone.now()
            provider.save()
            
            # Ajouter les documents d'identité s'ils n'existent pas
            if not provider.id_document_front:
                provider.id_document_front.save(
                    "id_front_test.png", create_test_image("id_front_test.png"), save=True
                )
            if not provider.id_document_back:
                provider.id_document_back.save(
                    "id_back_test.png", create_test_image("id_back_test.png"), save=True
                )
            
            self.stdout.write(
                self.style.SUCCESS(f"Prestataire mis à jour: {provider.name}")
            )
        elif existing_by_email:
            self.stdout.write(
                self.style.ERROR(
                    f"Un prestataire avec l'email '{email}' existe déjà pour un autre utilisateur."
                )
            )
            return
        elif existing_by_id:
            self.stdout.write(
                self.style.ERROR(
                    f"Un prestataire avec le numéro d'identité '{id_number}' existe déjà pour un autre utilisateur."
                )
            )
            return
        else:
            # Créer le prestataire avec tous les champs requis
            provider = ServiceProvider.objects.create(
                owner=user,
                name="Prestataire de Services Test",
                email=email,
                id_number=id_number,
                phone="+2250102030405",
                location="Plateau - Abidjan",
                description="Prestataire de test pour les services numériques et artisanaux.",
                services_overview="Création de sites web, gestion de réseaux sociaux, design graphique, et services artisanaux.",
                portfolio_url="https://example.com/portfolio",
                is_active=True,
                verification_status=ServiceProvider.STATUS_VERIFIED,
                verified_at=timezone.now(),
            )

            # Ajouter les documents d'identité (images de test)
            provider.id_document_front.save(
                "id_front_test.png", create_test_image("id_front_test.png"), save=True
            )
            provider.id_document_back.save(
                "id_back_test.png", create_test_image("id_back_test.png"), save=True
            )

            self.stdout.write(
                self.style.SUCCESS(f"Prestataire créé avec succès: {provider.name}")
            )

        # Afficher les informations
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Informations du prestataire ==="))
        self.stdout.write(f"Nom: {provider.name}")
        self.stdout.write(f"Email: {provider.email}")
        self.stdout.write(f"Numéro d'identité: {provider.id_number}")
        self.stdout.write(f"Téléphone: {provider.phone}")
        self.stdout.write(f"Localisation: {provider.location}")
        self.stdout.write(f"Statut de vérification: {provider.get_verification_status_display()}")
        self.stdout.write("")
        self.stdout.write("=== Informations de connexion ===")
        self.stdout.write(f"Identifiant: {username}")
        self.stdout.write(f"Mot de passe: {password}")
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Le prestataire est maintenant prêt à être utilisé pour les tests !"
            )
        )

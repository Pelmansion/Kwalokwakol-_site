"""
Commande pour créer un vendeur de test avec toutes les données nécessaires.
Usage: python manage.py create_test_vendor
"""
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image
import io

from marketplace.models import Vendor


class Command(BaseCommand):
    help = "Crée un vendeur de test avec toutes les données nécessaires (email, numéro d'identité, documents)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default="vendeur_test",
            help="Nom d'utilisateur pour le compte vendeur (défaut: vendeur_test).",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="vendeur.test@example.com",
            help="Email unique du vendeur (défaut: vendeur.test@example.com).",
        )
        parser.add_argument(
            "--id-number",
            type=str,
            default="CI-VENDOR-001",
            help="Numéro d'identité unique (défaut: CI-VENDOR-001).",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="vendeur123",
            help="Mot de passe pour le compte (défaut: vendeur123).",
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
                "first_name": "Vendeur",
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

        # Vérifier si un vendeur existe déjà avec cet owner
        existing_by_owner = Vendor.objects.filter(owner=user).first()
        existing_by_email = Vendor.objects.filter(email=email).exclude(owner=user).first()
        existing_by_id = Vendor.objects.filter(id_number=id_number).exclude(owner=user).first()

        if existing_by_owner:
            self.stdout.write(
                self.style.WARNING(
                    f"Un vendeur existe déjà pour cet utilisateur. Mise à jour de l'existant."
                )
            )
            vendor = existing_by_owner
            # Mettre à jour les champs requis
            vendor.email = email
            vendor.id_number = id_number
            vendor.name = "Boutique Test"
            vendor.phone = "0799633113"
            vendor.location = "Cocody - Abidjan"
            vendor.description = "Boutique de test pour les produits artisanaux et locaux."
            vendor.offer_type = Vendor.OFFER_BOTH
            vendor.services_overview = "Vente de produits locaux et services artisanaux."
            vendor.subscription_services = "Abonnements mensuels disponibles pour les clients fidèles."
            vendor.portfolio_url = "https://example.com/portfolio"
            vendor.is_active = True
            vendor.verification_status = Vendor.STATUS_PENDING
            vendor.save()
            
            # Ajouter les documents d'identité s'ils n'existent pas
            if not vendor.id_document_front:
                vendor.id_document_front.save(
                    "id_front_test.png", create_test_image("id_front_test.png"), save=True
                )
            if not vendor.id_document_back:
                vendor.id_document_back.save(
                    "id_back_test.png", create_test_image("id_back_test.png"), save=True
                )
            
            self.stdout.write(
                self.style.SUCCESS(f"Vendeur mis à jour: {vendor.name}")
            )
        elif existing_by_email:
            self.stdout.write(
                self.style.ERROR(
                    f"Un vendeur avec l'email '{email}' existe déjà pour un autre utilisateur."
                )
            )
            return
        elif existing_by_id:
            self.stdout.write(
                self.style.ERROR(
                    f"Un vendeur avec le numéro d'identité '{id_number}' existe déjà pour un autre utilisateur."
                )
            )
            return
        else:
            # Créer le vendeur avec tous les champs requis
            vendor = Vendor.objects.create(
                owner=user,
                name="Boutique Test",
                email=email,
                id_number=id_number,
                phone="0799633113",
                location="Cocody - Abidjan",
                description="Boutique de test pour les produits artisanaux et locaux.",
                offer_type=Vendor.OFFER_BOTH,
                services_overview="Vente de produits locaux et services artisanaux.",
                subscription_services="Abonnements mensuels disponibles pour les clients fidèles.",
                portfolio_url="https://example.com/portfolio",
                is_active=True,
                verification_status=Vendor.STATUS_PENDING,
            )

            # Ajouter les documents d'identité (images de test)
            vendor.id_document_front.save(
                "id_front_test.png", create_test_image("id_front_test.png"), save=True
            )
            vendor.id_document_back.save(
                "id_back_test.png", create_test_image("id_back_test.png"), save=True
            )

            self.stdout.write(
                self.style.SUCCESS(f"Vendeur créé avec succès: {vendor.name}")
            )

        # Afficher les informations
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Informations du vendeur ==="))
        self.stdout.write(f"Nom: {vendor.name}")
        self.stdout.write(f"Email: {vendor.email}")
        self.stdout.write(f"Numéro d'identité: {vendor.id_number}")
        self.stdout.write(f"Téléphone: {vendor.phone}")
        self.stdout.write(f"Localisation: {vendor.location}")
        self.stdout.write(f"Statut de vérification: {vendor.get_verification_status_display()}")
        self.stdout.write("")
        self.stdout.write("=== Informations de connexion ===")
        self.stdout.write(f"Identifiant: {username}")
        self.stdout.write(f"Mot de passe: {password}")
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "ATTENTION: Le vendeur est en attente de validation par un administrateur."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Le vendeur est maintenant prêt à être utilisé pour les tests !"
            )
        )

"""
Commande pour créer un utilisateur Admin et un utilisateur Super admin.
Usage: python manage.py create_admin_users
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import UserProfile


class Command(BaseCommand):
    help = "Crée un utilisateur Admin et un utilisateur Super admin (mot de passe par défaut à changer)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            type=str,
            default="admin123",
            help="Mot de passe commun pour les deux comptes (à changer après première connexion).",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Ne pas demander de confirmation.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        password = options["password"]
        no_input = options["no_input"]

        # --- Utilisateur Admin ---
        admin_user, admin_created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@kwalo.local",
                "first_name": "Admin",
                "last_name": "Plateforme",
                "is_staff": False,
                "is_superuser": False,
            },
        )
        if admin_created:
            admin_user.set_password(password)
            admin_user.save()
            profile, _ = UserProfile.objects.get_or_create(user=admin_user)
            profile.role = UserProfile.ROLE_ADMIN
            profile.save()
            self.stdout.write(self.style.SUCCESS("Utilisateur Admin créé: admin"))
        else:
            self.stdout.write("Utilisateur Admin existe déjà: admin")

        # --- Utilisateur Super admin ---
        super_user, super_created = User.objects.get_or_create(
            username="superadmin",
            defaults={
                "email": "superadmin@kwalo.local",
                "first_name": "Super",
                "last_name": "Admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if super_created:
            super_user.set_password(password)
            super_user.save()
            profile, _ = UserProfile.objects.get_or_create(user=super_user)
            profile.role = UserProfile.ROLE_SUPER_ADMIN
            profile.save()
            self.stdout.write(self.style.SUCCESS("Utilisateur Super admin créé: superadmin"))
        else:
            self.stdout.write("Utilisateur Super admin existe déjà: superadmin")

        self.stdout.write("")
        self.stdout.write("Connexion administration: /connexion-admin/")
        self.stdout.write("  - Admin:       identifiant « admin », mot de passe choisi (défaut: admin123)")
        self.stdout.write("  - Super admin: identifiant « superadmin », mot de passe choisi (défaut: admin123)")
        self.stdout.write("Pensez à changer les mots de passe après la première connexion.")

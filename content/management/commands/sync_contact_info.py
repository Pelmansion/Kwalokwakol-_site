from django.core.management.base import BaseCommand

from django.core.management import call_command


class Command(BaseCommand):
    help = "Met à jour la page Contact avec l'email et le téléphone officiels Kolê Group."

    def handle(self, *args, **options):
        call_command("sync_static_pages")

from django.core.management.base import BaseCommand

from content.models import StaticPage
from kwalo.static_pages import STATIC_PAGES


class Command(BaseCommand):
    help = "Met à jour toutes les pages statiques (FAQ, CGU, confidentialité, contact)."

    def handle(self, *args, **options):
        for page_def in STATIC_PAGES:
            page, created = StaticPage.objects.update_or_create(
                slug=page_def["slug"],
                defaults={
                    "title": page_def["title"],
                    "content": page_def["content"](),
                    "is_active": True,
                },
            )
            verb = "Créée" if created else "Mise à jour"
            self.stdout.write(self.style.SUCCESS(f"{verb} : /page/{page.slug}/"))

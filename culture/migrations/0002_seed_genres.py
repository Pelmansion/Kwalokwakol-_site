from django.db import migrations
from django.utils.text import slugify


DEFAULT_GENRES = [
    ("Coupé-décalé", "💃", 1),
    ("Zouglou", "🎶", 2),
    ("Reggae", "🎸", 3),
    ("Rap / Hip-hop", "🎤", 4),
    ("Afrobeat", "🥁", 5),
    ("Variété africaine", "🎵", 6),
    ("Gospel", "🙏", 7),
    ("R&B / Soul", "💖", 8),
    ("Traditionnel", "🪘", 9),
    ("Électro / DJ", "🎧", 10),
    ("Autre", "✨", 99),
]


def seed(apps, schema_editor):
    MusicGenre = apps.get_model("culture", "MusicGenre")
    for name, icon, order in DEFAULT_GENRES:
        slug = slugify(name)
        MusicGenre.objects.get_or_create(
            slug=slug, defaults={"name": name, "icon": icon, "display_order": order}
        )


def unseed(apps, schema_editor):
    MusicGenre = apps.get_model("culture", "MusicGenre")
    MusicGenre.objects.filter(slug__in=[slugify(n) for n, *_ in DEFAULT_GENRES]).delete()


class Migration(migrations.Migration):
    dependencies = [("culture", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]

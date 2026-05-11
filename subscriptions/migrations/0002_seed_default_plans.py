from decimal import Decimal

from django.db import migrations


DEFAULT_PLANS = [
    {
        "name": "Starter",
        "slug": "starter",
        "monthly_amount": Decimal("5000.00"),
        "target": "both",
        "tagline": "Pour démarrer et tester la plateforme",
        "description": "Idéal pour les petits vendeurs et prestataires qui démarrent.",
        "features": (
            "Jusqu'à 10 produits / services\n"
            "Profil public sur la marketplace\n"
            "Messagerie client\n"
            "Support par email"
        ),
        "is_featured": False,
        "display_order": 1,
    },
    {
        "name": "Pro",
        "slug": "pro",
        "monthly_amount": Decimal("15000.00"),
        "target": "both",
        "tagline": "Le choix des vendeurs réguliers",
        "description": "Pour les commerçants qui veulent vendre sérieusement.",
        "features": (
            "Produits / services illimités\n"
            "Boutique mise en avant sur la page d'accueil\n"
            "Messagerie client prioritaire\n"
            "Statistiques de ventes\n"
            "Support prioritaire"
        ),
        "is_featured": True,
        "display_order": 2,
    },
    {
        "name": "Premium",
        "slug": "premium",
        "monthly_amount": Decimal("30000.00"),
        "target": "both",
        "tagline": "Pour les professionnels exigeants",
        "description": "Visibilité maximale et fonctionnalités avancées.",
        "features": (
            "Tout ce qui est dans Pro\n"
            "Badge Premium visible sur votre profil\n"
            "Mise en avant dans les résultats de recherche\n"
            "Campagnes marketing incluses\n"
            "Support dédié 7j/7\n"
            "Commission réduite sur les ventes"
        ),
        "is_featured": False,
        "display_order": 3,
    },
]


def seed_plans(apps, schema_editor):
    Plan = apps.get_model("subscriptions", "SubscriptionPlan")
    for data in DEFAULT_PLANS:
        Plan.objects.update_or_create(slug=data["slug"], defaults=data)


def remove_plans(apps, schema_editor):
    Plan = apps.get_model("subscriptions", "SubscriptionPlan")
    Plan.objects.filter(slug__in=[p["slug"] for p in DEFAULT_PLANS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_plans, remove_plans),
    ]

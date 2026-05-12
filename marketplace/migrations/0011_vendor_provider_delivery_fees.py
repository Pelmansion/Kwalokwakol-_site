# Generated manually

from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0010_add_display_services_as_provider"),
    ]

    operations = [
        migrations.AddField(
            model_name="vendor",
            name="delivery_fee_standard",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("200"),
                help_text="Montant facturé pour l’option « Standard » lorsqu’un client commande vos produits (par commande regroupant votre boutique).",
                max_digits=12,
                verbose_name="Frais livraison standard (FCFA)",
            ),
        ),
        migrations.AddField(
            model_name="vendor",
            name="delivery_fee_express",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("500"),
                help_text="Montant facturé pour l’option « Express » lorsqu’un client commande vos produits.",
                max_digits=12,
                verbose_name="Frais livraison express (FCFA)",
            ),
        ),
        migrations.AddField(
            model_name="serviceprovider",
            name="delivery_fee_standard",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("200"),
                help_text="Pour vos produits vendus sans boutique (profil prestataire uniquement), option livraison standard.",
                max_digits=12,
                verbose_name="Frais livraison standard (FCFA)",
            ),
        ),
        migrations.AddField(
            model_name="serviceprovider",
            name="delivery_fee_express",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("500"),
                help_text="Pour vos produits vendus sans boutique, option livraison express.",
                max_digits=12,
                verbose_name="Frais livraison express (FCFA)",
            ),
        ),
    ]

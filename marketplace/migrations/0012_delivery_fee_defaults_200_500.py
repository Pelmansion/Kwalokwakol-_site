# Tarifs par défaut : standard 200 FCFA, express 500 FCFA

from decimal import Decimal

from django.db import migrations, models


def forwards_update_old_defaults(apps, schema_editor):
    Vendor = apps.get_model("marketplace", "Vendor")
    ServiceProvider = apps.get_model("marketplace", "ServiceProvider")
    old_std = Decimal("2500")
    old_exp = Decimal("5000")
    new_std = Decimal("200")
    new_exp = Decimal("500")
    Vendor.objects.filter(
        delivery_fee_standard=old_std,
        delivery_fee_express=old_exp,
    ).update(delivery_fee_standard=new_std, delivery_fee_express=new_exp)
    ServiceProvider.objects.filter(
        delivery_fee_standard=old_std,
        delivery_fee_express=old_exp,
    ).update(delivery_fee_standard=new_std, delivery_fee_express=new_exp)


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0011_vendor_provider_delivery_fees"),
    ]

    operations = [
        migrations.RunPython(forwards_update_old_defaults, backwards_noop),
        migrations.AlterField(
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
        migrations.AlterField(
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
        migrations.AlterField(
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
        migrations.AlterField(
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

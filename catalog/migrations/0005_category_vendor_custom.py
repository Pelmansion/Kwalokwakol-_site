# Generated manually for vendor-owned categories

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0004_alter_product_vendor"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(max_length=120),
        ),
        migrations.AddField(
            model_name="category",
            name="service_provider",
            field=models.ForeignKey(
                blank=True,
                help_text="Si renseigné : catégorie propre à ce prestataire.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="custom_categories",
                to="marketplace.serviceprovider",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="vendor",
            field=models.ForeignKey(
                blank=True,
                help_text="Si renseigné : catégorie propre à cette boutique.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="custom_categories",
                to="marketplace.vendor",
            ),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(vendor__isnull=False, service_provider__isnull=True)
                    | models.Q(vendor__isnull=True, service_provider__isnull=False)
                    | models.Q(vendor__isnull=True, service_provider__isnull=True)
                ),
                name="category_at_most_one_owner",
            ),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                condition=models.Q(vendor__isnull=False),
                fields=("vendor", "name"),
                name="category_unique_vendor_name",
            ),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                condition=models.Q(service_provider__isnull=False),
                fields=("service_provider", "name"),
                name="category_unique_provider_name",
            ),
        ),
    ]

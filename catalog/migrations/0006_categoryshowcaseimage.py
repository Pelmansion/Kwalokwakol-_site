# Generated manually for category showcase (vitrine) images

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0005_category_vendor_custom"),
        ("marketplace", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CategoryShowcaseImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="catalog/category_showcase/%Y/%m/")),
                ("caption", models.CharField(blank=True, max_length=200, verbose_name="légende")),
                ("position", models.PositiveSmallIntegerField(default=0)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="showcase_images",
                        to="catalog.category",
                    ),
                ),
                (
                    "service_provider",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="category_showcase_images",
                        to="marketplace.serviceprovider",
                    ),
                ),
                (
                    "vendor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="category_showcase_images",
                        to="marketplace.vendor",
                    ),
                ),
            ],
            options={
                "ordering": ["position", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="categoryshowcaseimage",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(vendor__isnull=False, service_provider__isnull=True)
                    | models.Q(vendor__isnull=True, service_provider__isnull=False)
                ),
                name="category_showcase_one_owner",
            ),
        ),
        migrations.AddIndex(
            model_name="categoryshowcaseimage",
            index=models.Index(fields=["category", "vendor", "position"], name="ctgshw_cv_pos"),
        ),
        migrations.AddIndex(
            model_name="categoryshowcaseimage",
            index=models.Index(
                fields=["category", "service_provider", "position"],
                name="ctgshw_csp_pos",
            ),
        ),
    ]

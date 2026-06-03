from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0008_rename_ctgshw_cv_pos_catalog_cat_categor_427b5b_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="catalog/products/%Y/%m/",
                verbose_name="photo du produit",
            ),
        ),
    ]

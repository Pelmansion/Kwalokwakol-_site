# Generated manually for GeniusPay (référence checkout)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("culture", "0002_seed_genres"),
    ]

    operations = [
        migrations.AddField(
            model_name="songpurchase",
            name="genius_reference",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="ticket",
            name="genius_reference",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
    ]

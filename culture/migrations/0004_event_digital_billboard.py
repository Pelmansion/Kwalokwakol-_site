# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("culture", "0003_songpurchase_ticket_genius_reference"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="digital_billboard",
            field=models.ImageField(
                blank=True,
                help_text="Bâche numérique large (visuel promotionnel : date, lieu, tarifs, artistes…).",
                null=True,
                upload_to="culture/events/billboards/",
            ),
        ),
    ]

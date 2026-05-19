# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0006_categoryshowcaseimage"),
    ]

    operations = [
        migrations.AddField(
            model_name="categoryshowcaseimage",
            name="showcase_kind",
            field=models.CharField(
                choices=[
                    ("general", "Général"),
                    ("chambre", "Chambre"),
                    ("salle_eau", "Salle d'eau / toilettes"),
                    ("lit", "Literie"),
                    ("accueil", "Accueil / hall"),
                    ("restauration", "Restauration / petit-déjeuner"),
                    ("exterieur", "Extérieur / piscine / jardin"),
                    ("autre", "Autre"),
                ],
                default="general",
                help_text="Utile pour hôtels / résidences : chambre, salle d'eau, accueil, etc.",
                max_length=20,
                verbose_name="type d'espace",
            ),
        ),
    ]

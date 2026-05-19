from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_userprofile_avatar_userprofile_role"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="avatar",
            field=models.ImageField(
                blank=True,
                help_text="Visible dans l’en-tête et la navigation après connexion.",
                null=True,
                upload_to="avatars/",
                verbose_name="photo de profil",
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="cover_photo",
            field=models.ImageField(
                blank=True,
                help_text="Bandeau large sous la barre du site une fois connecté (optionnel).",
                null=True,
                upload_to="user_covers/",
                verbose_name="photo de couverture",
            ),
        ),
    ]

# Generated manually
from django.db import migrations, models


def populate_vendor_emails(apps, schema_editor):
    """Remplir les emails NULL des boutiques avec une valeur basée sur le nom."""
    Vendor = apps.get_model("marketplace", "Vendor")
    for vendor in Vendor.objects.filter(email__isnull=True):
        base_email = f"{vendor.name.lower().replace(' ', '_')}@boutique.local"
        counter = 1
        email = base_email
        while Vendor.objects.filter(email=email).exclude(pk=vendor.pk).exists():
            email = f"{base_email.split('@')[0]}{counter}@boutique.local"
            counter += 1
        vendor.email = email
        vendor.save()


def populate_vendor_id_numbers(apps, schema_editor):
    """Remplir les numéros d'identité NULL des boutiques avec une valeur temporaire."""
    Vendor = apps.get_model("marketplace", "Vendor")
    for vendor in Vendor.objects.filter(id_number__isnull=True):
        id_number = f"TEMP_VENDOR_{vendor.pk}"
        counter = 1
        while Vendor.objects.filter(id_number=id_number).exclude(pk=vendor.pk).exists():
            id_number = f"TEMP_VENDOR_{vendor.pk}_{counter}"
            counter += 1
        vendor.id_number = id_number
        vendor.save()


def populate_serviceprovider_emails(apps, schema_editor):
    """Remplir les emails NULL des prestataires avec une valeur basée sur le nom."""
    ServiceProvider = apps.get_model("marketplace", "ServiceProvider")
    for sp in ServiceProvider.objects.filter(email__isnull=True):
        base_email = f"{sp.name.lower().replace(' ', '_')}@prestataire.local"
        counter = 1
        email = base_email
        while ServiceProvider.objects.filter(email=email).exclude(pk=sp.pk).exists():
            email = f"{base_email.split('@')[0]}{counter}@prestataire.local"
            counter += 1
        sp.email = email
        sp.save()


def populate_serviceprovider_id_numbers(apps, schema_editor):
    """Remplir les numéros d'identité NULL des prestataires avec une valeur temporaire."""
    ServiceProvider = apps.get_model("marketplace", "ServiceProvider")
    for sp in ServiceProvider.objects.filter(id_number__isnull=True):
        id_number = f"TEMP_SP_{sp.pk}"
        counter = 1
        while ServiceProvider.objects.filter(id_number=id_number).exclude(pk=sp.pk).exists():
            id_number = f"TEMP_SP_{sp.pk}_{counter}"
            counter += 1
        sp.id_number = id_number
        sp.save()


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0007_alter_serviceprovider_id_number_and_more'),
    ]

    operations = [
        # Remplir les emails NULL (boutiques)
        migrations.RunPython(populate_vendor_emails, migrations.RunPython.noop),
        # Remplir les numéros d'identité NULL (boutiques)
        migrations.RunPython(populate_vendor_id_numbers, migrations.RunPython.noop),
        # Remplir les emails NULL (prestataires)
        migrations.RunPython(populate_serviceprovider_emails, migrations.RunPython.noop),
        # Remplir les numéros d'identité NULL (prestataires)
        migrations.RunPython(populate_serviceprovider_id_numbers, migrations.RunPython.noop),
        # Rendre l'email obligatoire
        migrations.AlterField(
            model_name='vendor',
            name='email',
            field=models.EmailField(help_text="Email unique de la boutique", unique=True),
        ),
        # Rendre le numéro d'identité obligatoire
        migrations.AlterField(
            model_name='vendor',
            name='id_number',
            field=models.CharField(help_text="Numéro d'identité unique", max_length=50, unique=True),
        ),
        # Rendre les documents obligatoires
        migrations.AlterField(
            model_name='vendor',
            name='id_document_front',
            field=models.ImageField(help_text="Pièce d'identité recto", upload_to='kyc/vendor/id_front/'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='id_document_back',
            field=models.ImageField(help_text="Pièce d'identité verso", upload_to='kyc/vendor/id_back/'),
        ),
        # Prestataires : rendre l'email obligatoire
        migrations.AlterField(
            model_name='serviceprovider',
            name='email',
            field=models.EmailField(help_text="Email unique du prestataire de services", unique=True),
        ),
        # Prestataires : rendre le numéro d'identité obligatoire
        migrations.AlterField(
            model_name='serviceprovider',
            name='id_number',
            field=models.CharField(help_text="Numéro d'identité unique du prestataire", max_length=50, unique=True),
        ),
        # Prestataires : rendre les documents obligatoires
        migrations.AlterField(
            model_name='serviceprovider',
            name='id_document_front',
            field=models.ImageField(help_text="Pièce d'identité recto", upload_to='kyc/service_provider/id_front/'),
        ),
        migrations.AlterField(
            model_name='serviceprovider',
            name='id_document_back',
            field=models.ImageField(help_text="Pièce d'identité verso", upload_to='kyc/service_provider/id_back/'),
        ),
    ]

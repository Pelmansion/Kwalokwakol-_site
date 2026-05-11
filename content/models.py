from django.db import models
from django.utils.text import slugify


class StaticPage(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    content = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class HomepageBackground(models.Model):
    """Image de fond affichée sur le slide principal de la page d'accueil.

    Une seule image peut être active à la fois : activer une image désactive
    automatiquement les autres. L'admin peut supprimer l'entrée pour revenir
    au visuel statique par défaut.
    """

    image = models.ImageField(upload_to="homepage/backgrounds/")
    title = models.CharField(
        max_length=120,
        blank=True,
        help_text="Libellé interne (facultatif), pour vous y retrouver.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Image de fond (accueil)"
        verbose_name_plural = "Images de fond (accueil)"

    def __str__(self):
        return self.title or f"Fond d'accueil #{self.pk}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            HomepageBackground.objects.exclude(pk=self.pk).filter(is_active=True).update(
                is_active=False
            )

    def delete(self, *args, **kwargs):
        image = self.image
        result = super().delete(*args, **kwargs)
        if image:
            image.delete(save=False)
        return result

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).first()

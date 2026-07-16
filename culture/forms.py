from django import forms
from django.forms import modelformset_factory

from .models import ArtistProfile, Event, Song, TicketCategory
from .widgets import CultureSplitDateTimeWidget, FeaturedArtistsWidget


class ArtistProfileForm(forms.ModelForm):
    class Meta:
        model = ArtistProfile
        fields = [
            "stage_name",
            "bio",
            "primary_genre",
            "region",
            "city",
            "portrait",
            "cover_photo",
            "phone",
            "whatsapp",
            "email",
            "website",
            "facebook",
            "instagram",
            "youtube",
            "tiktok",
            "spotify",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5, "placeholder": "Présente-toi, ton parcours, ton univers..."}),
            "stage_name": forms.TextInput(attrs={"placeholder": "Ex: Yelo Star"}),
            "city": forms.TextInput(attrs={"placeholder": "Ex: Korhogo"}),
            "region": forms.TextInput(attrs={"placeholder": "Ex: Poro"}),
            "phone": forms.TextInput(attrs={"placeholder": "0799633113"}),
            "whatsapp": forms.TextInput(attrs={"placeholder": "0799633113"}),
            "portrait": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"}
            ),
            "cover_photo": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"}
            ),
        }


class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = [
            "title",
            "cover_image",
            "audio_file",
            "genre",
            "description",
            "lyrics",
            "release_date",
            "duration_seconds",
            "pricing",
            "price_fcfa",
            "allow_streaming",
            "is_published",
        ]
        widgets = {
            "release_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "lyrics": forms.Textarea(attrs={"rows": 6}),
            "duration_seconds": forms.NumberInput(attrs={"min": 0, "placeholder": "Ex: 215"}),
            "price_fcfa": forms.NumberInput(attrs={"min": 0, "step": 50}),
            "cover_image": forms.FileInput(
                attrs={
                    "accept": "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp",
                    "class": "culture-form__file-input",
                }
            ),
            "audio_file": forms.FileInput(
                attrs={
                    "accept": "audio/mpeg,audio/wav,audio/mp3,.mp3,.wav",
                    "class": "culture-form__file-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["audio_file"].required = False
            self.fields["cover_image"].required = False
        price_field = self.fields["price_fcfa"]
        _orig_to_python = price_field.to_python

        def to_python(value):
            if isinstance(value, str):
                value = value.strip().replace("\u00a0", "").replace(" ", "").replace(",", ".")
            return _orig_to_python(value)

        price_field.to_python = to_python

    def clean_cover_image(self):
        if self.data.get("cover_image-clear") == "on":
            return None
        uploaded = self.files.get("cover_image")
        if uploaded:
            return uploaded
        if self.instance.pk and self.instance.cover_image:
            return self.instance.cover_image
        return None

    def clean_audio_file(self):
        if self.data.get("audio_file-clear") == "on":
            raise forms.ValidationError("Le fichier audio est obligatoire.")
        uploaded = self.files.get("audio_file")
        if uploaded:
            return uploaded
        if self.instance.pk and self.instance.audio_file:
            return self.instance.audio_file
        raise forms.ValidationError("Ajoutez un fichier audio (MP3 ou WAV).")

    def clean(self):
        cleaned = super().clean()
        pricing = cleaned.get("pricing")
        price = cleaned.get("price_fcfa")
        if pricing == Song.PRICING_PAID and (not price or price <= 0):
            self.add_error(
                "price_fcfa", "Indiquez un prix supérieur à 0 pour une chanson payante."
            )
        return cleaned


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "poster",
            "digital_billboard",
            "description",
            "starts_at",
            "ends_at",
            "venue_name",
            "address",
            "city",
            "region",
            "map_url",
            "headlining_artist",
            "featured_artists",
            "status",
            "is_published",
        ]
        widgets = {
            "starts_at": CultureSplitDateTimeWidget(),
            "ends_at": CultureSplitDateTimeWidget(),
            "description": forms.Textarea(attrs={"rows": 5}),
            "title": forms.TextInput(attrs={"placeholder": "Ex: Festival Korhogo Live 2026"}),
            "venue_name": forms.TextInput(attrs={"placeholder": "Ex: Stade municipal"}),
            "city": forms.TextInput(attrs={"placeholder": "Ex: Abidjan"}),
            "region": forms.TextInput(attrs={"placeholder": "Ex: Lagunes"}),
            "poster": forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"}),
            "digital_billboard": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"}
            ),
            "featured_artists": FeaturedArtistsWidget(),
        }

    def __init__(self, *args, artist: ArtistProfile | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if artist:
            self.fields["headlining_artist"].initial = artist
            self.fields["featured_artists"].queryset = ArtistProfile.objects.filter(is_active=True).exclude(pk=artist.pk)


class TicketCategoryForm(forms.ModelForm):
    class Meta:
        model = TicketCategory
        fields = ["name", "description", "price_fcfa", "quantity_total", "color", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ex: Standard / VIP / VVIP"}),
            "description": forms.TextInput(attrs={"placeholder": "Avantages inclus (optionnel)"}),
            "price_fcfa": forms.NumberInput(attrs={"min": 0, "step": 100}),
            "quantity_total": forms.NumberInput(attrs={"min": 1, "placeholder": "Ex: 100"}),
            "color": forms.TextInput(attrs={"type": "color", "class": "culture-form__color"}),
        }


TicketCategoryFormSet = modelformset_factory(
    TicketCategory,
    form=TicketCategoryForm,
    extra=3,
    max_num=12,
    can_delete=False,
)


class TicketBuyerForm(forms.Form):
    """Acheteur d'un billet — utilisable par anonyme ou connecté."""

    buyer_name = forms.CharField(label="Votre nom complet", max_length=120)
    buyer_email = forms.EmailField(label="Email")
    buyer_phone = forms.CharField(label="Téléphone (WhatsApp)", max_length=30, required=False)
    quantity = forms.IntegerField(label="Nombre de billets", min_value=1, max_value=10, initial=1)

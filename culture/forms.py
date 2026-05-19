from django import forms

from .models import ArtistProfile, Event, Song, TicketCategory


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
            "phone": forms.TextInput(attrs={"placeholder": "+225 ..."}),
            "whatsapp": forms.TextInput(attrs={"placeholder": "+225 ..."}),
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
        }

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
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 5}),
            "title": forms.TextInput(attrs={"placeholder": "Ex: Festival Korhogo Live 2026"}),
            "venue_name": forms.TextInput(attrs={"placeholder": "Ex: Stade municipal"}),
            "city": forms.TextInput(attrs={"placeholder": "Ex: Abidjan"}),
            "region": forms.TextInput(attrs={"placeholder": "Ex: Lagunes"}),
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
            "name": forms.TextInput(attrs={"placeholder": "Ex: Standard / VIP / Carré Or"}),
            "description": forms.TextInput(attrs={"placeholder": "Avantages inclus (optionnel)"}),
            "price_fcfa": forms.NumberInput(attrs={"min": 0, "step": 100}),
            "quantity_total": forms.NumberInput(attrs={"min": 1}),
            "color": forms.TextInput(attrs={"type": "color"}),
        }


class TicketBuyerForm(forms.Form):
    """Acheteur d'un billet — utilisable par anonyme ou connecté."""

    buyer_name = forms.CharField(label="Votre nom complet", max_length=120)
    buyer_email = forms.EmailField(label="Email")
    buyer_phone = forms.CharField(label="Téléphone (WhatsApp)", max_length=30, required=False)
    quantity = forms.IntegerField(label="Nombre de billets", min_value=1, max_value=10, initial=1)

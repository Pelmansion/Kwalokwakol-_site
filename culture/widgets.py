from django import forms


class CultureSplitDateTimeWidget(forms.SplitDateTimeWidget):
    """Date et heure séparées — évite le sélecteur datetime-local qui reste ouvert (Chrome/Edge)."""

    template_name = "culture/widgets/split_datetime_widget.html"

    def __init__(self, attrs=None):
        super().__init__(
            attrs=attrs,
            date_attrs={"type": "date", "class": "culture-form__date"},
            time_attrs={"type": "time", "class": "culture-form__time", "step": "60"},
        )


class FeaturedArtistsWidget(forms.SelectMultiple):
    """Liste d'artistes invités : saisie + puces, au lieu du select multiple natif."""

    template_name = "culture/widgets/featured_artists_widget.html"

    class Media:
        js = ("js/featured-artists-picker.js",)

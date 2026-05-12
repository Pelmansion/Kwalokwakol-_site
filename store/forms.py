from django import forms

from marketplace.models import ServiceRequest
from orders.models import Order


def _genius_available() -> bool:
    from payments.genius import is_configured

    return is_configured()


class PaymentRadioSelect(forms.RadioSelect):
    """Désactive les moyens non disponibles ; GeniusPay si les clés API sont présentes."""

    DISABLED_METHODS = frozenset(
        {Order.METHOD_CARD, Order.METHOD_MOBILE, Order.METHOD_PAYPAL}
    )

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if str(value) in self.DISABLED_METHODS:
            option["attrs"]["disabled"] = True
        return option


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "full_name",
            "phone",
            "email",
            "address",
            "city",
            "delivery_option",
            "payment_method",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        payment_field = self.fields["payment_method"]
        payment_field.widget = PaymentRadioSelect(attrs={"class": "payment-options"})
        choices = [
            (Order.METHOD_LOCAL, "Espèces à la livraison"),
        ]
        if _genius_available():
            choices.insert(
                0,
                (
                    Order.METHOD_GENIUS,
                    "Paiement en ligne (Wave, Orange Money, MTN MoMo, carte… via GeniusPay)",
                ),
            )
        choices.extend(
            [
                (Order.METHOD_CARD, "Carte bancaire (bientôt)"),
                (Order.METHOD_MOBILE, "Mobile Money (bientôt)"),
                (Order.METHOD_PAYPAL, "PayPal (bientôt)"),
            ]
        )
        payment_field.choices = choices
        payment_field.initial = (
            Order.METHOD_GENIUS if _genius_available() else Order.METHOD_LOCAL
        )

    def clean_payment_method(self):
        value = self.cleaned_data.get("payment_method")
        if value == Order.METHOD_GENIUS:
            if not _genius_available():
                raise forms.ValidationError("Le paiement en ligne n'est pas disponible pour le moment.")
            return value
        if value == Order.METHOD_LOCAL:
            return value
        raise forms.ValidationError("Ce moyen de paiement n'est pas encore activé.")

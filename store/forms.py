from django import forms

from marketplace.models import ServiceRequest
from orders.models import Order


def _genius_available() -> bool:
    from payments.genius import is_configured

    return is_configured()


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
        payment_field.widget = forms.RadioSelect(attrs={"class": "payment-options"})
        if _genius_available():
            choices = [
                (
                    Order.METHOD_GENIUS,
                    "Paiement en ligne — Wave, Orange Money, MTN MoMo, carte bancaire",
                ),
                (Order.METHOD_LOCAL, "Espèces à la livraison"),
            ]
        else:
            choices = [(Order.METHOD_LOCAL, "Espèces à la livraison")]
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


class ServiceRequestForm(forms.ModelForm):
    is_interested = forms.BooleanField(
        required=True, initial=True, label="Je suis intéressé par ce service"
    )

    class Meta:
        model = ServiceRequest
        fields = ["is_interested", "comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Expliquez votre besoin..."}
            )
        }

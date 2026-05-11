from django import forms

from marketplace.models import ServiceRequest
from orders.models import Order


class PaymentRadioSelect(forms.RadioSelect):
    """RadioSelect qui désactive tous les moyens de paiement sauf les espèces."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if str(value) != Order.METHOD_LOCAL:
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
        payment_field.choices = [
            (Order.METHOD_CARD, "Carte bancaire"),
            (Order.METHOD_MOBILE, "Mobile Money"),
            (Order.METHOD_PAYPAL, "PayPal"),
            (Order.METHOD_LOCAL, "Espèces"),
        ]
        payment_field.initial = Order.METHOD_LOCAL

    def clean_payment_method(self):
        value = self.cleaned_data.get("payment_method")
        if value != Order.METHOD_LOCAL:
            raise forms.ValidationError(
                "Pour le moment, seul le paiement en espèces est disponible."
            )
        return value


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

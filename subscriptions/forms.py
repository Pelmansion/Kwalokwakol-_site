from decimal import Decimal

from django import forms

from .models import Subscription, SubscriptionPlan


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "name",
            "monthly_amount",
            "target",
            "tagline",
            "description",
            "features",
            "is_active",
            "is_featured",
            "display_order",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "features": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Une fonctionnalité par ligne"}
            ),
        }


class AdminSetAmountForm(forms.Form):
    """Formulaire admin pour fixer un abonnement (plan + montant personnalisé)."""

    plan = forms.ModelChoiceField(
        queryset=SubscriptionPlan.objects.filter(is_active=True),
        required=False,
        label="Formule suggérée",
        empty_label="— Montant personnalisé (sans formule) —",
    )
    monthly_amount = forms.DecimalField(
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        label="Montant mensuel (FCFA)",
    )
    admin_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Note interne (optionnelle)"}),
        label="Note admin",
    )

    def __init__(self, *args, target: str = "both", **kwargs):
        super().__init__(*args, **kwargs)
        if target == "vendor":
            self.fields["plan"].queryset = SubscriptionPlan.objects.filter(
                is_active=True, target__in=[SubscriptionPlan.TARGET_VENDOR, SubscriptionPlan.TARGET_BOTH]
            )
        elif target == "provider":
            self.fields["plan"].queryset = SubscriptionPlan.objects.filter(
                is_active=True, target__in=[SubscriptionPlan.TARGET_PROVIDER, SubscriptionPlan.TARGET_BOTH]
            )


class ChoosePlanForm(forms.Form):
    """Formulaire côté vendeur/prestataire pour choisir une formule."""

    plan = forms.ModelChoiceField(
        queryset=SubscriptionPlan.objects.filter(is_active=True),
        widget=forms.RadioSelect,
        empty_label=None,
        label="Formule",
    )

    def __init__(self, *args, target: str = "both", **kwargs):
        super().__init__(*args, **kwargs)
        if target == "vendor":
            self.fields["plan"].queryset = SubscriptionPlan.objects.filter(
                is_active=True, target__in=[SubscriptionPlan.TARGET_VENDOR, SubscriptionPlan.TARGET_BOTH]
            )
        elif target == "provider":
            self.fields["plan"].queryset = SubscriptionPlan.objects.filter(
                is_active=True, target__in=[SubscriptionPlan.TARGET_PROVIDER, SubscriptionPlan.TARGET_BOTH]
            )

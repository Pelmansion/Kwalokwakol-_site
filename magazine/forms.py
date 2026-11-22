from django import forms

from .models import MagazineSubscriptionPlan, PartnershipInquiry


class PartnershipInquiryForm(forms.ModelForm):
    class Meta:
        model = PartnershipInquiry
        fields = ["name", "organization", "email", "phone", "offer_type", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Votre nom"}),
            "organization": forms.TextInput(attrs={"placeholder": "Organisation"}),
            "email": forms.EmailInput(attrs={"placeholder": "email@exemple.com"}),
            "phone": forms.TextInput(attrs={"placeholder": "Téléphone"}),
            "message": forms.Textarea(attrs={"rows": 5, "placeholder": "Votre message…"}),
        }


class MagazineSubscribeForm(forms.Form):
    plan = forms.ModelChoiceField(
        queryset=MagazineSubscriptionPlan.objects.filter(is_active=True),
        label="Formule",
        empty_label=None,
    )
    full_name = forms.CharField(max_length=160, label="Nom complet")
    email = forms.EmailField(label="E-mail")
    phone = forms.CharField(max_length=30, required=False, label="Téléphone")

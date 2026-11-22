from django import forms

from .models import (
    MagazineNewsletterSignup,
    MagazineSubscriptionPlan,
    PartnershipInquiry,
    PersonalitySubmission,
)


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


class PersonalitySubmissionForm(forms.ModelForm):
    class Meta:
        model = PersonalitySubmission
        fields = [
            "first_name",
            "last_name",
            "profession",
            "locality",
            "region",
            "bio",
            "achievements",
            "email",
            "phone",
            "photo",
            "consent",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "Prénom"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Nom"}),
            "profession": forms.TextInput(attrs={"placeholder": "Profession / domaine"}),
            "locality": forms.TextInput(attrs={"placeholder": "Localité d'origine"}),
            "region": forms.TextInput(attrs={"placeholder": "Région"}),
            "bio": forms.Textarea(attrs={"rows": 4, "placeholder": "Parcours…"}),
            "achievements": forms.Textarea(attrs={"rows": 3, "placeholder": "Réalisations…"}),
            "email": forms.EmailInput(attrs={"placeholder": "email@exemple.com"}),
            "phone": forms.TextInput(attrs={"placeholder": "Téléphone"}),
        }
        labels = {
            "consent": "J'autorise Dan Prestige Magazine à traiter et publier ces informations.",
        }

    def clean_consent(self):
        consent = self.cleaned_data.get("consent")
        if not consent:
            raise forms.ValidationError("Le consentement est obligatoire pour soumettre une demande.")
        return consent


class MagazineNewsletterForm(forms.ModelForm):
    class Meta:
        model = MagazineNewsletterSignup
        fields = ["full_name", "email"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Votre nom (optionnel)"}),
            "email": forms.EmailInput(attrs={"placeholder": "email@exemple.com", "required": True}),
        }
        labels = {
            "full_name": "Nom",
            "email": "E-mail",
        }

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("Indiquez une adresse e-mail.")
        return email

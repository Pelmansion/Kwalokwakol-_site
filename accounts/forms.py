from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .auth_backends import resolve_login_to_user
from .models import Address, UserProfile


class LoginFormWithInactiveMessage(AuthenticationForm):
    """Formulaire de connexion qui affiche un message clair si le compte n'est pas encore activé (email non vérifié)."""

    def clean(self):
        super().clean()
        if self.errors.get("__all__"):
            raw = (self.cleaned_data.get("username") if self.cleaned_data else None) or (
                self.data.get("username") if self.data else ""
            )
            if raw:
                user = resolve_login_to_user(raw)
                if user and not user.is_active:
                    self._errors.pop("__all__", None)
                    self.add_error(
                        None,
                        "Ce compte n'est pas encore activé. Consultez votre boîte mail et cliquez sur le lien de confirmation.",
                    )
        return self.cleaned_data


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    avatar = forms.ImageField(required=False)
    phone = forms.CharField(required=False, max_length=30)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=commit)
        from .models import UserProfile

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.phone = self.cleaned_data.get("phone", "")
        avatar = self.cleaned_data.get("avatar")
        if avatar:
            profile.avatar = avatar
        profile.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["avatar", "cover_photo", "phone", "default_address", "city"]
        labels = {
            "avatar": "Photo de profil",
            "cover_photo": "Photo de couverture",
            "phone": "Téléphone",
            "default_address": "Adresse",
            "city": "Ville",
        }
        help_texts = {
            "avatar": "Affichée dans la barre du haut, le menu compte et la navigation mobile.",
            "cover_photo": "Bandeau décoratif sous la barre du site lorsque vous êtes connecté.",
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["label", "address", "city", "phone", "is_default"]

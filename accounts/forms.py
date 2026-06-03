from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .auth_backends import resolve_login_to_user
from .media_utils import clear_old_image_before_upload, uploaded_image_file, validate_profile_image
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
    avatar = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"}))
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
        widgets = {
            "avatar": forms.FileInput(
                attrs={
                    "accept": "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp",
                }
            ),
            "cover_photo": forms.FileInput(
                attrs={
                    "accept": "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp",
                }
            ),
        }

    def clean_avatar(self):
        uploaded = uploaded_image_file(self.files, "avatar")
        if uploaded:
            validate_profile_image(uploaded, label="Photo de profil")
            return uploaded
        if self.instance.pk and self.instance.avatar:
            return self.instance.avatar
        return None

    def clean_cover_photo(self):
        uploaded = uploaded_image_file(self.files, "cover_photo")
        if uploaded:
            validate_profile_image(uploaded, label="Photo de couverture")
            return uploaded
        if self.instance.pk and self.instance.cover_photo:
            return self.instance.cover_photo
        return None

    def save(self, commit=True):
        avatar_new = uploaded_image_file(self.files, "avatar")
        cover_new = uploaded_image_file(self.files, "cover_photo")
        clear_old_image_before_upload(self.instance, "avatar", new_upload=avatar_new)
        clear_old_image_before_upload(self.instance, "cover_photo", new_upload=cover_new)
        profile = super().save(commit=False)
        if commit:
            profile.save()
            self.save_m2m()
        return profile


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["label", "address", "city", "phone", "is_default"]

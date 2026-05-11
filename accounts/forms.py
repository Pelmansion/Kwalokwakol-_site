from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Address, UserProfile


class LoginFormWithInactiveMessage(AuthenticationForm):
    """Formulaire de connexion qui affiche un message clair si le compte n'est pas encore activé (email non vérifié)."""

    def clean(self):
        super().clean()
        if self.errors.get("__all__"):
            username = self.cleaned_data.get("username") or (self.data.get("username") if self.data else None)
            if username:
                try:
                    user = User.objects.get(username=username)
                    if not user.is_active:
                        self._errors.pop("__all__", None)
                        self.add_error(
                            None,
                            "Ce compte n'est pas encore activé. Consultez votre boîte mail et cliquez sur le lien de confirmation.",
                        )
                except User.DoesNotExist:
                    pass
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
        fields = ["avatar", "phone", "default_address", "city"]


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["label", "address", "city", "phone", "is_default"]

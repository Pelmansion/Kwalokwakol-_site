from django import forms

from catalog.models import Category, Product
from orders.models import Order

from .models import ServiceProvider, Vendor


class VendorForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="Email de la boutique",
        help_text="Cet email doit être unique (parmi toutes les boutiques et prestataires) et sera utilisé pour identifier votre boutique"
    )
    id_number = forms.CharField(
        required=True,
        max_length=50,
        label="Numéro d'identité",
        help_text="Numéro d'identité unique (CNI, passeport, etc.) - doit être unique parmi toutes les boutiques et prestataires"
    )
    id_document_front = forms.ImageField(
        required=True,
        label="Pièce d'identité recto",
        help_text="Photo ou scan de votre pièce d'identité (recto)"
    )
    id_document_back = forms.ImageField(
        required=True,
        label="Pièce d'identité verso",
        help_text="Photo ou scan de votre pièce d'identité (verso)"
    )
    
    class Meta:
        model = Vendor
        fields = [
            "name",
            "description",
            "offer_type",
            "services_overview",
            "subscription_services",
            "portfolio_url",
            "phone",
            "email",
            "location",
            "id_number",
            "id_document_front",
            "id_document_back",
            "profile_photo",
        ]
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Vérifier l'unicité globale de l'email (boutiques ET prestataires)
            existing_vendor = Vendor.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance.pk else None).first()
            if existing_vendor:
                raise forms.ValidationError("Une boutique avec cet email existe déjà.")
            existing_provider = ServiceProvider.objects.filter(email=email).first()
            if existing_provider:
                raise forms.ValidationError("Un prestataire avec cet email existe déjà.")
        return email
    
    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        if id_number:
            # Vérifier l'unicité globale du numéro d'identité (boutiques ET prestataires)
            existing_vendor = Vendor.objects.filter(id_number=id_number).exclude(pk=self.instance.pk if self.instance.pk else None).first()
            if existing_vendor:
                raise forms.ValidationError("Une boutique avec ce numéro d'identité existe déjà.")
            existing_provider = ServiceProvider.objects.filter(id_number=id_number).first()
            if existing_provider:
                raise forms.ValidationError("Un prestataire avec ce numéro d'identité existe déjà.")
        return id_number


class ProductForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=True,
        label="Catégorie",
        help_text="Sélectionnez la catégorie à laquelle appartient votre produit ou service"
    )
    name = forms.CharField(
        required=True,
        max_length=200,
        label="Nom",
        help_text="Nom du produit ou service"
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
        label="Description",
        help_text="Description détaillée du produit ou service"
    )
    price = forms.DecimalField(
        required=True,
        max_digits=12,
        decimal_places=2,
        label="Prix",
        help_text="Prix en FCFA"
    )
    stock = forms.IntegerField(
        required=True,
        min_value=0,
        label="Stock",
        help_text="Quantité disponible en stock"
    )
    kind = forms.ChoiceField(
        required=True,
        choices=Product.KIND_CHOICES,
        label="Type",
        help_text="Sélectionnez si c'est un produit ou un service"
    )
    image_url = forms.URLField(
        required=False,
        label="URL de l'image",
        help_text="Lien vers une image du produit ou service"
    )
    
    class Meta:
        model = Product
        fields = ["category", "name", "description", "price", "stock", "kind", "image_url"]


class VendorProfileForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="Email de la boutique",
        help_text="Cet email doit être unique (parmi toutes les boutiques et prestataires) et sera utilisé pour identifier votre boutique"
    )
    id_number = forms.CharField(
        required=True,
        max_length=50,
        label="Numéro d'identité",
        help_text="Numéro d'identité unique (CNI, passeport, etc.) - doit être unique parmi toutes les boutiques et prestataires"
    )
    
    class Meta:
        model = Vendor
        fields = [
            "name",
            "description",
            "offer_type",
            "services_overview",
            "subscription_services",
            "portfolio_url",
            "phone",
            "email",
            "location",
            "id_number",
            "id_document_front",
            "id_document_back",
            "profile_photo",
        ]
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Vérifier l'unicité globale de l'email (boutiques ET prestataires)
            existing_vendor = Vendor.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance.pk else None).first()
            if existing_vendor:
                raise forms.ValidationError("Une boutique avec cet email existe déjà.")
            existing_provider = ServiceProvider.objects.filter(email=email).first()
            if existing_provider:
                raise forms.ValidationError("Un prestataire avec cet email existe déjà.")
        return email
    
    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        if id_number:
            # Vérifier l'unicité globale du numéro d'identité (boutiques ET prestataires)
            existing_vendor = Vendor.objects.filter(id_number=id_number).exclude(pk=self.instance.pk if self.instance.pk else None).first()
            if existing_vendor:
                raise forms.ValidationError("Une boutique avec ce numéro d'identité existe déjà.")
            existing_provider = ServiceProvider.objects.filter(id_number=id_number).first()
            if existing_provider:
                raise forms.ValidationError("Un prestataire avec ce numéro d'identité existe déjà.")
        return id_number


class ServiceProviderForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="Email du prestataire",
        help_text="Cet email doit être unique (parmi toutes les boutiques et prestataires) et sera utilisé pour identifier votre profil prestataire",
    )
    id_number = forms.CharField(
        required=True,
        max_length=50,
        label="Numéro d'identité",
        help_text="Numéro d'identité unique (CNI, passeport, etc.) - doit être unique parmi toutes les boutiques et prestataires",
    )
    id_document_front = forms.ImageField(
        required=True,
        label="Pièce d'identité recto",
        help_text="Photo ou scan de votre pièce d'identité (recto)",
    )
    id_document_back = forms.ImageField(
        required=True,
        label="Pièce d'identité verso",
        help_text="Photo ou scan de votre pièce d'identité (verso)",
    )
    display_services_as_provider = forms.BooleanField(
        required=False,
        initial=False,
        label="Ce sont mes propres services que je propose",
        help_text="Cochez cette case pour afficher vos offres en fiche prestataire (photo, badges, localisation). Sinon vos services s'afficheront comme les produits classiques.",
    )

    class Meta:
        model = ServiceProvider
        fields = [
            "name",
            "description",
            "services_overview",
            "portfolio_url",
            "phone",
            "email",
            "location",
            "id_number",
            "id_document_front",
            "id_document_back",
            "profile_photo",
            "display_services_as_provider",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            # Vérifier l'unicité globale de l'email (boutiques ET prestataires)
            existing_vendor = Vendor.objects.filter(email=email).first()
            if existing_vendor:
                raise forms.ValidationError("Une boutique avec cet email existe déjà.")
            existing_provider = (
                ServiceProvider.objects.filter(email=email)
                .exclude(pk=self.instance.pk if self.instance.pk else None)
                .first()
            )
            if existing_provider:
                raise forms.ValidationError(
                    "Un prestataire avec cet email existe déjà."
                )
        return email

    def clean_id_number(self):
        id_number = self.cleaned_data.get("id_number")
        if id_number:
            # Vérifier l'unicité globale du numéro d'identité (boutiques ET prestataires)
            existing_vendor = Vendor.objects.filter(id_number=id_number).first()
            if existing_vendor:
                raise forms.ValidationError("Une boutique avec ce numéro d'identité existe déjà.")
            existing_provider = (
                ServiceProvider.objects.filter(id_number=id_number)
                .exclude(pk=self.instance.pk if self.instance.pk else None)
                .first()
            )
            if existing_provider:
                raise forms.ValidationError(
                    "Un prestataire avec ce numéro d'identité existe déjà."
                )
        return id_number


class ServiceProviderProfileForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="Email du prestataire",
        help_text="Cet email doit être unique (parmi toutes les boutiques et prestataires) et sera utilisé pour identifier votre profil prestataire",
    )
    id_number = forms.CharField(
        required=True,
        max_length=50,
        label="Numéro d'identité",
        help_text="Numéro d'identité unique (CNI, passeport, etc.) - doit être unique parmi toutes les boutiques et prestataires",
    )

    class Meta:
        model = ServiceProvider
        fields = [
            "name",
            "description",
            "services_overview",
            "portfolio_url",
            "phone",
            "email",
            "location",
            "id_number",
            "id_document_front",
            "id_document_back",
            "profile_photo",
            "display_services_as_provider",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            # Vérifier l'unicité globale de l'email (boutiques ET prestataires)
            existing_vendor = Vendor.objects.filter(email=email).first()
            if existing_vendor:
                raise forms.ValidationError("Une boutique avec cet email existe déjà.")
            existing_provider = (
                ServiceProvider.objects.filter(email=email)
                .exclude(pk=self.instance.pk if self.instance.pk else None)
                .first()
            )
            if existing_provider:
                raise forms.ValidationError(
                    "Un prestataire avec cet email existe déjà."
                )
        return email

    def clean_id_number(self):
        id_number = self.cleaned_data.get("id_number")
        if id_number:
            # Vérifier l'unicité globale du numéro d'identité (boutiques ET prestataires)
            existing_vendor = Vendor.objects.filter(id_number=id_number).first()
            if existing_vendor:
                raise forms.ValidationError("Une boutique avec ce numéro d'identité existe déjà.")
            existing_provider = (
                ServiceProvider.objects.filter(id_number=id_number)
                .exclude(pk=self.instance.pk if self.instance.pk else None)
                .first()
            )
            if existing_provider:
                raise forms.ValidationError(
                    "Un prestataire avec ce numéro d'identité existe déjà."
                )
        return id_number


class ServiceProductForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=True,
        label="Catégorie",
        help_text="Sélectionnez la catégorie à laquelle appartient votre service"
    )
    name = forms.CharField(
        required=True,
        max_length=200,
        label="Nom du service",
        help_text="Nom du service proposé"
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
        label="Description",
        help_text="Description détaillée du service"
    )
    price = forms.DecimalField(
        required=True,
        max_digits=12,
        decimal_places=2,
        label="Prix",
        help_text="Prix en FCFA"
    )
    image_url = forms.URLField(
        required=False,
        label="URL de l'image",
        help_text="Lien vers une image illustrant le service"
    )
    
    class Meta:
        model = Product
        fields = ["category", "name", "description", "price", "image_url"]


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status", "tracking_code"]

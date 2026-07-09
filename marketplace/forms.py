from django import forms
from django.db.models import Q

from accounts.media_utils import clear_old_image_before_upload, uploaded_image_file, validate_profile_image
from catalog.models import Category, CategoryShowcaseImage, Product
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


def marketplace_category_queryset(*, vendor=None, service_provider=None):
    """Catégories plateforme + celles créées par ce vendeur / ce prestataire."""
    q = Q(vendor__isnull=True, service_provider__isnull=True)
    if vendor is not None:
        q |= Q(vendor=vendor)
    if service_provider is not None:
        q |= Q(service_provider=service_provider)
    return Category.objects.filter(is_active=True).filter(q).distinct().order_by("name")


class ProductForm(forms.ModelForm):
    new_category = forms.CharField(
        required=False,
        max_length=120,
        label="Ou créer une catégorie",
        widget=forms.TextInput(
            attrs={"placeholder": "Ex. : Épices artisanales, Accessoires…"}
        ),
        help_text="Optionnel : si le nom correspond à une catégorie du site (ex. « Epices » → Épices), "
        "le produit sera classé dans la catégorie commune. Sinon, catégorie propre à votre boutique.",
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="— Choisir une catégorie existante —",
        label="Catégorie",
        help_text="Catégories générales du site ou celles que vous avez déjà créées.",
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
        label="URL de l'image (optionnel)",
        help_text="Si vous n'uploadez pas de fichier, vous pouvez coller un lien vers une image en ligne.",
    )

    class Meta:
        model = Product
        fields = [
            "category",
            "name",
            "description",
            "price",
            "stock",
            "kind",
            "image",
            "image_url",
        ]
        widgets = {
            "image": forms.FileInput(
                attrs={
                    "accept": "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp",
                }
            ),
        }
        labels = {
            "image": "Photo du produit",
        }
        help_texts = {
            "image": "JPEG ou PNG — affichée dans la boutique. Prioritaire sur l'URL ci-dessous.",
        }

    def __init__(self, *args, vendor=None, **kwargs):
        self._vendor = vendor
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = marketplace_category_queryset(vendor=vendor)
        if self.instance and self.instance.pk:
            self.fields["image"].required = False

    def clean_image(self):
        uploaded = uploaded_image_file(self.files, "image")
        if uploaded:
            validate_profile_image(uploaded, label="Photo du produit")
            return uploaded
        if self.instance.pk and self.instance.image:
            return self.instance.image
        return None

    def save(self, commit=True):
        image_new = uploaded_image_file(self.files, "image")
        clear_old_image_before_upload(self.instance, "image", new_upload=image_new)
        product = super().save(commit=False)
        if commit:
            product.save()
            self.save_m2m()
        return product

    def clean(self):
        cleaned = super().clean()
        new = (cleaned.get("new_category") or "").strip()
        cat = cleaned.get("category")
        if new and cat:
            raise forms.ValidationError(
                "Choisissez une catégorie dans la liste ou indiquez un nouveau nom, pas les deux."
            )
        if not new and not cat:
            self.add_error(
                "category",
                "Sélectionnez une catégorie existante ou créez-en une nouvelle (champ ci-dessous).",
            )
        return cleaned


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
            "delivery_fee_standard",
            "delivery_fee_express",
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
            "delivery_fee_standard",
            "delivery_fee_express",
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
    new_category = forms.CharField(
        required=False,
        max_length=120,
        label="Ou créer une catégorie",
        widget=forms.TextInput(attrs={"placeholder": "Ex. : Réparation, Coiffure à domicile…"}),
        help_text="Optionnel : si le nom correspond à une catégorie du site, le service sera classé "
        "dans la catégorie commune. Sinon, rubrique propre à votre activité.",
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="— Choisir une catégorie existante —",
        label="Catégorie",
        help_text="Catégories générales du site ou celles que vous avez déjà créées.",
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
        label="URL de l'image (optionnel)",
        help_text="Si vous n'uploadez pas de fichier, vous pouvez coller un lien vers une image en ligne.",
    )

    class Meta:
        model = Product
        fields = ["category", "name", "description", "price", "image", "image_url"]
        widgets = {
            "image": forms.FileInput(
                attrs={
                    "accept": "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp",
                }
            ),
        }
        labels = {
            "image": "Photo du service",
        }
        help_texts = {
            "image": "JPEG ou PNG — affichée dans la boutique. Prioritaire sur l'URL ci-dessous.",
        }

    def __init__(self, *args, service_provider=None, **kwargs):
        self._service_provider = service_provider
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = marketplace_category_queryset(
            service_provider=service_provider
        )
        if self.instance and self.instance.pk:
            self.fields["image"].required = False

    def clean_image(self):
        uploaded = uploaded_image_file(self.files, "image")
        if uploaded:
            validate_profile_image(uploaded, label="Photo du service")
            return uploaded
        if self.instance.pk and self.instance.image:
            return self.instance.image
        return None

    def save(self, commit=True):
        image_new = uploaded_image_file(self.files, "image")
        clear_old_image_before_upload(self.instance, "image", new_upload=image_new)
        product = super().save(commit=False)
        if commit:
            product.save()
            self.save_m2m()
        return product

    def clean(self):
        cleaned = super().clean()
        new = (cleaned.get("new_category") or "").strip()
        cat = cleaned.get("category")
        if new and cat:
            raise forms.ValidationError(
                "Choisissez une catégorie dans la liste ou indiquez un nouveau nom, pas les deux."
            )
        if not new and not cat:
            self.add_error(
                "category",
                "Sélectionnez une catégorie existante ou créez-en une nouvelle (champ ci-dessous).",
            )
        return cleaned


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status", "tracking_code"]


class CategoryShowcaseImageForm(forms.ModelForm):
    class Meta:
        model = CategoryShowcaseImage
        fields = ["image", "caption", "showcase_kind"]
        labels = {
            "image": "Photo",
            "caption": "Légende (optionnelle)",
            "showcase_kind": "Type d'espace",
        }
        help_texts = {
            "image": "JPEG ou PNG — plats, chambres, accueil, etc.",
            "caption": "Ex. : suite vue mer, plat du jour…",
            "showcase_kind": "Pour hôtels / résidences : indiquez chambre, salle d'eau, hall…",
        }

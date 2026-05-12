from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.models import Category, Product, ProductMedia
from content.models import StaticPage
from marketplace.models import ServiceProvider, ServiceRequest, Vendor
from notifications.models import Notification
from orders.models import Order, OrderItem, OrderStatusHistory
from payments.models import Payment
from reviews.models import Review, ReviewReply
from messaging.models import Message, Thread


class Command(BaseCommand):
    help = "Créer des données de test pour le site"

    def handle(self, *args, **options):
        User = get_user_model()
        vendor_user, created_user = User.objects.get_or_create(
            username="vendeur_test",
            defaults={
                "email": "vendeur@test.local",
                "first_name": "Vendeur",
                "last_name": "Test",
            },
        )
        if created_user:
            vendor_user.set_password("vendeur123")
            vendor_user.save()

        provider_user, created_provider_user = User.objects.get_or_create(
            username="prestataire_test",
            defaults={
                "email": "prestataire@test.local",
                "first_name": "Prestataire",
                "last_name": "Test",
            },
        )
        if created_provider_user:
            provider_user.set_password("prestataire123")
            provider_user.save()

        client_user, created_client_user = User.objects.get_or_create(
            username="client_test",
            defaults={
                "email": "client@test.local",
                "first_name": "Client",
                "last_name": "Test",
            },
        )
        if created_client_user:
            client_user.set_password("client123")
            client_user.save()

        categories = [
            ("Alimentation", "Boulangerie, boucherie, pâtisserie, produits frais."),
            ("Métiers du bâtiment", "Maçonnerie, plomberie, électricité, menuiserie."),
            ("Production", "Fabrication d'objets, artisanat local, ateliers."),
            ("Services artisanaux", "Coiffure, couture, esthétique, imprimerie."),
            ("Électroménager", "Appareils pour la maison et le bureau."),
            ("Boutiques", "Boutiques locales et revendeurs spécialisés."),
            ("Produits vivriers", "Légumes, fruits, céréales, vivriers."),
            ("Outils numériques", "Services et solutions digitales pour particuliers et PME."),
        ]

        vendors = [
            ("Atelier Kouassi", "Cocody - Abidjan", "Menuiserie et fabrication."),
            ("Boulangerie Brio", "Yopougon - Abidjan", "Pains et pâtisseries."),
            ("Maison Kéita", "Plateau - Abidjan", "Couture et mode africaine."),
            ("Techno Home", "Marcory - Abidjan", "Électroménager et SAV."),
            ("Fleuriste Aïcha", "Treichville - Abidjan", "Décoration et événementiel."),
            ("Agence Digitale KWL", "Plateau - Abidjan", "Services numériques et outils digitaux."),
        ]

        created_categories = []
        for name, description in categories:
            category, _ = Category.objects.get_or_create(
                name=name,
                vendor__isnull=True,
                service_provider__isnull=True,
                defaults={"description": description, "is_active": True},
            )
            created_categories.append(category)

        created_vendors = []
        for name, location, description in vendors:
            vendor, _ = Vendor.objects.get_or_create(
                name=name,
                defaults={
                    "location": location,
                    "description": description,
                    "is_active": True,
                },
            )
            created_vendors.append(vendor)

        # Un seul vendeur peut être lié à vendor_user (OneToOneField owner)
        vendor_test, _ = Vendor.objects.get_or_create(
            owner=vendor_user,
            defaults={
                "name": "Vendeur Test",
                "location": "Cocody - Abidjan",
                "description": "Boutique de test pour les vendeurs.",
                "is_active": True,
                "verification_status": Vendor.STATUS_VERIFIED,
                "verified_at": timezone.now(),
                "email": "vendeur_test@example.local",
                "id_number": "VTEST-0001",
                "id_document_front": "kyc/vendor/id_front/default.png",
                "id_document_back": "kyc/vendor/id_back/default.png",
            },
        )
        # S'assurer que le vendeur de test est bien vérifié/actif
        vendor_test.is_active = True
        vendor_test.verification_status = Vendor.STATUS_VERIFIED
        vendor_test.verified_at = timezone.now()
        vendor_test.save()
        created_vendors.append(vendor_test)

        # Un seul prestataire peut être lié à provider_user (OneToOneField owner)
        service_provider, _ = ServiceProvider.objects.get_or_create(
            owner=provider_user,
            defaults={
                "name": "Prestataire Test",
                "location": "Plateau - Abidjan",
                "description": "Prestataire de services numériques.",
                "is_active": True,
                "verification_status": ServiceProvider.STATUS_VERIFIED,
                "verified_at": timezone.now(),
                "phone": "+2250102030405",
                "email": "prestataire_test@example.local",
                "id_number": "SPTEST-0001",
                "id_document_front": "kyc/service_provider/id_front/default.png",
                "id_document_back": "kyc/service_provider/id_back/default.png",
            },
        )
        service_provider.is_active = True
        service_provider.verification_status = ServiceProvider.STATUS_VERIFIED
        service_provider.verified_at = timezone.now()
        service_provider.save()

        sample_products = [
            # Alimentation
            ("Pain complet", "Alimentation", "Boulangerie Brio", 5000, Product.PRODUCT),
            ("Gâteau d'anniversaire", "Alimentation", "Boulangerie Brio", 15000, Product.PRODUCT),
            ("Baguette croustillante", "Alimentation", "Boulangerie Brio", 300, Product.PRODUCT),
            ("Pack petit-déjeuner", "Alimentation", "Boulangerie Brio", 2500, Product.PRODUCT),
            # Métiers du bâtiment
            ("Pose de carrelage", "Métiers du bâtiment", "Atelier Kouassi", 45000, Product.SERVICE),
            ("Réparation fuite d'eau", "Métiers du bâtiment", "Atelier Kouassi", 20000, Product.SERVICE),
            ("Peinture salon 4 murs", "Métiers du bâtiment", "Atelier Kouassi", 35000, Product.SERVICE),
            # Production
            ("Étagère sur mesure", "Production", "Atelier Kouassi", 30000, Product.PRODUCT),
            ("Table basse en bois", "Production", "Atelier Kouassi", 55000, Product.PRODUCT),
            ("Commode 3 tiroirs", "Production", "Atelier Kouassi", 80000, Product.PRODUCT),
            # Services artisanaux
            ("Coiffure tresses", "Services artisanaux", "Maison Kéita", 12000, Product.SERVICE),
            ("Robe sur mesure", "Services artisanaux", "Maison Kéita", 65000, Product.PRODUCT),
            ("Retouche pantalon", "Services artisanaux", "Maison Kéita", 3000, Product.SERVICE),
            ("Maquillage événementiel", "Services artisanaux", "Maison Kéita", 20000, Product.SERVICE),
            # Électroménager
            ("Réfrigérateur 2 portes", "Électroménager", "Techno Home", 250000, Product.PRODUCT),
            ("Machine à laver", "Électroménager", "Techno Home", 180000, Product.PRODUCT),
            ("Ventilateur sur pied", "Électroménager", "Techno Home", 35000, Product.PRODUCT),
            ("Bouilloire électrique", "Électroménager", "Techno Home", 12000, Product.PRODUCT),
            # Boutiques / déco
            ("Bouquet premium", "Boutiques", "Fleuriste Aïcha", 25000, Product.PRODUCT),
            ("Décoration mariage", "Boutiques", "Fleuriste Aïcha", 150000, Product.SERVICE),
            ("Bouquet simple", "Boutiques", "Fleuriste Aïcha", 10000, Product.PRODUCT),
            ("Centre de table fleuri", "Boutiques", "Fleuriste Aïcha", 18000, Product.PRODUCT),
            # Produits vivriers
            ("Panier légumes", "Produits vivriers", "Boulangerie Brio", 8000, Product.PRODUCT),
            ("Sac de riz 25kg", "Produits vivriers", "Techno Home", 22000, Product.PRODUCT),
            ("Filet d'oranges", "Produits vivriers", "Boulangerie Brio", 3500, Product.PRODUCT),
            ("Plantains mûrs (lot)", "Produits vivriers", "Boulangerie Brio", 2500, Product.PRODUCT),
            # Outils numériques
            ("Licence Office 365", "Outils numériques", "Agence Digitale KWL", 35000, Product.PRODUCT),
            ("Confection de CV professionnel", "Outils numériques", "Agence Digitale KWL", 12000, Product.SERVICE),
            ("Création de site vitrine", "Outils numériques", "Agence Digitale KWL", 180000, Product.SERVICE),
            ("Gestion de page Facebook", "Outils numériques", "Agence Digitale KWL", 45000, Product.SERVICE),
            ("Pack outils numériques", "Outils numériques", "Agence Digitale KWL", 60000, Product.PRODUCT),
            ("Campagne pub Facebook", "Outils numériques", "Agence Digitale KWL", 90000, Product.SERVICE),
            # Vendeur test
            ("Vitrine PVC", "Production", "Vendeur Test", 40000, Product.PRODUCT),
            ("Maintenance site web", "Outils numériques", "Vendeur Test", 80000, Product.SERVICE),
        ]

        created = 0
        for idx, (name, category_name, vendor_name, price, kind) in enumerate(
            sample_products, start=1
        ):
            category = next(
                (cat for cat in created_categories if cat.name == category_name), None
            )
            vendor = next(
                (ven for ven in created_vendors if ven.name == vendor_name), None
            )
            product, was_created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "category": category,
                    "vendor": vendor,
                    "price": price,
                    "stock": 0 if kind == Product.SERVICE else 25,
                    "kind": kind,
                    "is_active": True,
                    "description": "Produit/service de qualité proposé par nos artisans.",
                },
            )
            if was_created:
                ProductMedia.objects.create(
                    product=product,
                    media_type=ProductMedia.IMAGE,
                    url=f"https://picsum.photos/seed/kwalo-{idx}/600/400",
                    is_primary=True,
                )
                created += 1

        # S'assurer d'avoir au moins 60 produits actifs pour bien remplir la page d'accueil
        total_products = Product.objects.filter(is_active=True).count()
        if total_products < 60:
            needed = 60 - total_products
            base_category = created_categories[0] if created_categories else None
            base_vendor = vendor_test if "vendor_test" in locals() else (created_vendors[0] if created_vendors else None)
            for extra in range(needed):
                name = f"Produit test automatique #{extra + 1}"
                product, was_created = Product.objects.get_or_create(
                    name=name,
                    defaults={
                        "category": base_category,
                        "vendor": base_vendor,
                        "price": 1000 + extra * 200,
                        "stock": 20,
                        "kind": Product.PRODUCT,
                        "is_active": True,
                        "description": "Produit de test généré automatiquement pour le remplissage des listes.",
                    },
                )
                if was_created:
                    ProductMedia.objects.create(
                        product=product,
                        media_type=ProductMedia.IMAGE,
                        url=f"https://picsum.photos/seed/kwalo-auto-{extra}/600/400",
                        is_primary=True,
                    )
                    created += 1

        service_products = [
            ("Conception site vitrine", "Outils numériques", 180000),
            ("Audit référencement SEO", "Outils numériques", 90000),
            ("Maintenance applicative", "Outils numériques", 75000),
        ]
        for idx, (name, category_name, price) in enumerate(service_products, start=101):
            category = next(
                (cat for cat in created_categories if cat.name == category_name), None
            )
            product, was_created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "category": category,
                    "service_provider": service_provider,
                    "price": price,
                    "stock": 0,
                    "kind": Product.SERVICE,
                    "is_active": True,
                    "description": "Service professionnel proposé par un prestataire.",
                },
            )
            if was_created:
                ProductMedia.objects.create(
                    product=product,
                    media_type=ProductMedia.IMAGE,
                    url=f"https://picsum.photos/seed/kwalo-service-{idx}/600/400",
                    is_primary=True,
                )
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Données de test prêtes. Produits ajoutés: {created}."
            )
        )

        StaticPage.objects.get_or_create(
            title="FAQ",
            defaults={"content": "Questions fréquentes et réponses principales."},
        )
        StaticPage.objects.get_or_create(
            title="Conditions générales",
            defaults={"content": "Conditions d'utilisation du site."},
        )
        StaticPage.objects.get_or_create(
            title="Confidentialité",
            defaults={"content": "Politique de confidentialité des données."},
        )
        StaticPage.objects.get_or_create(
            slug="contact",
            defaults={
                "title": "Contact",
                "content": (
                    "Besoin d'aide ou d'informations ? Écrivez-nous à "
                    "contact@kwalok-wakole.ci ou appelez le +225 00 00 00 00."
                ),
            },
        )

        product_items = Product.objects.filter(kind=Product.PRODUCT, is_active=True)[:6]
        if product_items:
            order, created_order = Order.objects.get_or_create(
                full_name="Client Test",
                phone="+2250700000000",
                email="client@test.local",
                address="Cocody, Rue des Jardins",
                city="Abidjan",
                delivery_option=Order.DELIVERY_STANDARD,
                payment_method=Order.METHOD_MOBILE,
                defaults={
                    "user": client_user,
                    "delivery_fee": 200,
                    "status": Order.STATUS_PAID,
                    "payment_status": Order.PAYMENT_SUCCESS,
                },
            )
            if created_order:
                subtotal = 0
                for product in product_items[:3]:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=2,
                        unit_price=product.price,
                    )
                    subtotal += float(product.price) * 2
                order.total_amount = subtotal + float(order.delivery_fee)
                order.save()
                Payment.objects.create(
                    order=order,
                    provider=Payment.PROVIDER_MOBILE,
                    status=Payment.STATUS_SUCCESS,
                    amount=order.total_amount,
                    reference="PAY-TEST-001",
                )
                OrderStatusHistory.objects.create(
                    order=order, status=Order.STATUS_PAID, note="Paiement validé."
                )

            order2, created_order2 = Order.objects.get_or_create(
                full_name="Client Test",
                phone="+2250700000000",
                email="client@test.local",
                address="Cocody, Rue des Jardins",
                city="Abidjan",
                delivery_option=Order.DELIVERY_EXPRESS,
                payment_method=Order.METHOD_CARD,
                defaults={
                    "user": client_user,
                    "delivery_fee": 500,
                    "status": Order.STATUS_PENDING,
                    "payment_status": Order.PAYMENT_PENDING,
                },
            )
            if created_order2:
                subtotal = 0
                for product in product_items[3:6]:
                    OrderItem.objects.create(
                        order=order2,
                        product=product,
                        quantity=1,
                        unit_price=product.price,
                    )
                    subtotal += float(product.price)
                order2.total_amount = subtotal + float(order2.delivery_fee)
                order2.save()
                Payment.objects.create(
                    order=order2,
                    provider=Payment.PROVIDER_CARD,
                    status=Payment.STATUS_PENDING,
                    amount=order2.total_amount,
                    reference="PAY-TEST-002",
                )
                OrderStatusHistory.objects.create(
                    order=order2, status=Order.STATUS_PENDING, note="Commande créée."
                )

        review_product = Product.objects.filter(vendor=vendor_test, kind=Product.PRODUCT).first()
        if review_product:
            review, created_review = Review.objects.get_or_create(
                product=review_product,
                user=client_user,
                defaults={
                    "rating": 5,
                    "comment": "Produit excellent, livraison rapide.",
                    "is_approved": True,
                },
            )
            if created_review:
                ReviewReply.objects.create(
                    review=review,
                    vendor=vendor_test,
                    message="Merci pour votre confiance !",
                )

        service_product_vendor = Product.objects.filter(
            vendor=vendor_test, kind=Product.SERVICE
        ).first()
        if service_product_vendor:
            service_request, created_request = ServiceRequest.objects.get_or_create(
                service=service_product_vendor,
                customer=client_user,
                defaults={
                    "vendor": vendor_test,
                    "is_interested": True,
                    "comment": "Je veux un devis rapide pour ce service.",
                    "status": ServiceRequest.STATUS_APPROVED,
                },
            )
            if created_request:
                Notification.objects.create(
                    user=client_user,
                    title="Demande de service validée",
                    body=f"Votre demande pour {service_product_vendor.name} a été validée.",
                    kind=Notification.INFO,
                )

        service_product_provider = Product.objects.filter(
            service_provider=service_provider, kind=Product.SERVICE
        ).first()
        if service_product_provider:
            ServiceRequest.objects.get_or_create(
                service=service_product_provider,
                customer=client_user,
                defaults={
                    "service_provider": service_provider,
                    "is_interested": True,
                    "comment": "Je suis intéressé par ce service.",
                    "status": ServiceRequest.STATUS_PENDING,
                },
            )

        thread, _ = Thread.objects.get_or_create(user=client_user, vendor=vendor_test)
        Message.objects.get_or_create(
            thread=thread,
            sender=client_user,
            body="Bonjour, je souhaite en savoir plus sur vos offres.",
        )

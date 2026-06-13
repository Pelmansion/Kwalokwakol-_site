"""Contenu des pages statiques Kolê Group (FAQ, CGU, confidentialité, contact)."""

from kwalo.contact_info import (
    KOLE_CONTACT_EMAIL,
    KOLE_CONTACT_PHONE,
    KOLE_CONTACT_PHONE_INTL,
    KOLE_WHATSAPP_WA_ME,
    contact_page_content,
)

__all__ = [
    "STATIC_PAGES",
    "contact_page_content",
    "faq_page_content",
    "conditions_generales_content",
    "confidentialite_content",
]


def faq_page_content() -> str:
    return f"""
<p>Retrouvez ici les réponses aux questions les plus fréquentes sur <strong>Kolê Group</strong> : achats, livraison, paiement, espace vendeur et Kolê Culture.</p>

<h2>Compte et inscription</h2>
<ul>
  <li><strong>Comment créer un compte ?</strong> Cliquez sur <em>Compte → Créer un compte</em>, renseignez votre e-mail et choisissez un mot de passe. Vous recevrez un e-mail de vérification.</li>
  <li><strong>Puis-je me connecter avec mon numéro ?</strong> Oui, si votre numéro est enregistré dans votre profil, il peut servir d'identifiant de connexion.</li>
  <li><strong>J'ai oublié mon mot de passe.</strong> Utilisez le lien <em>Mot de passe oublié</em> sur la page de connexion pour recevoir un e-mail de réinitialisation.</li>
</ul>

<h2>Commandes et livraison</h2>
<ul>
  <li><strong>Comment passer commande ?</strong> Ajoutez des articles au panier, validez votre adresse et votre téléphone, puis confirmez la commande.</li>
  <li><strong>Quels sont les délais de livraison ?</strong> En zone urbaine, comptez en général 24 à 48 h. En zone rurale ou selon le vendeur, 2 à 5 jours ouvrés.</li>
  <li><strong>La livraison est-elle gratuite ?</strong> La livraison gratuite s'applique à partir de <strong>15 000 FCFA</strong> d'achat lorsque l'offre est proposée sur le produit ou par le vendeur.</li>
  <li><strong>Comment suivre ma commande ?</strong> Rendez-vous dans <em>Compte → Mes commandes</em> pour consulter le statut (en préparation, expédiée, livrée).</li>
</ul>

<h2>Paiement</h2>
<ul>
  <li><strong>Quels moyens de paiement acceptez-vous ?</strong> Paiement en ligne via <strong>GeniusPay</strong> (Wave, Orange Money, MTN MoMo, carte bancaire selon disponibilité) et, lorsque proposé, paiement en espèces à la livraison.</li>
  <li><strong>Mon paiement est-il sécurisé ?</strong> Les transactions en ligne sont traitées par notre partenaire de paiement. Kolê Group ne conserve pas vos coordonnées bancaires complètes.</li>
  <li><strong>Je n'ai pas reçu de confirmation.</strong> Vérifiez vos spams, puis contactez-nous avec la référence de commande.</li>
</ul>

<h2>Retours et litiges</h2>
<ul>
  <li><strong>Puis-je retourner un produit ?</strong> Vous disposez de <strong>7 jours</strong> après réception pour signaler un problème (produit défectueux, non conforme, endommagé).</li>
  <li><strong>Comment contacter le vendeur ?</strong> Utilisez la messagerie intégrée à votre commande pour échanger directement avec lui.</li>
  <li><strong>En cas de litige ?</strong> Si aucune solution n'est trouvée, écrivez à <a href="mailto:{KOLE_CONTACT_EMAIL}">{KOLE_CONTACT_EMAIL}</a> en joignant votre numéro de commande.</li>
</ul>

<h2>Vendeurs et prestataires</h2>
<ul>
  <li><strong>Comment ouvrir une boutique ?</strong> Rendez-vous sur <em>Devenir vendeur</em>, complétez le formulaire et choisissez une formule d'abonnement adaptée.</li>
  <li><strong>Comment proposer des services ?</strong> Créez un profil prestataire via <em>Devenir prestataire</em> (hébergement, location, services professionnels, etc.).</li>
  <li><strong>Quand suis-je payé ?</strong> Les règles de versement dépendent de votre formule et du statut des commandes livrées ; consultez votre tableau de bord vendeur.</li>
</ul>

<h2>Kolê Culture</h2>
<ul>
  <li><strong>Comment acheter un billet de concert ?</strong> Parcourez les événements, sélectionnez vos places et payez en ligne. Vous recevez un billet avec QR code.</li>
  <li><strong>Comment utiliser mon billet ?</strong> Présentez le QR code (imprimé ou sur téléphone) à l'entrée ; une fois scanné, le billet ne peut plus être réutilisé.</li>
  <li><strong>Puis-je devenir artiste ?</strong> Oui, activez votre profil artiste depuis la section Kolê Culture pour publier titres et annoncer vos concerts.</li>
</ul>

<h2>Autre question ?</h2>
<p>Notre équipe est disponible du lundi au samedi :</p>
<ul>
  <li>E-mail : <a href="mailto:{KOLE_CONTACT_EMAIL}">{KOLE_CONTACT_EMAIL}</a></li>
  <li>Téléphone / WhatsApp : <a href="tel:{KOLE_CONTACT_PHONE_INTL}">{KOLE_CONTACT_PHONE}</a></li>
  <li><a href="https://wa.me/{KOLE_WHATSAPP_WA_ME}" target="_blank" rel="noopener">Écrire sur WhatsApp</a></li>
</ul>
"""


def conditions_generales_content() -> str:
    return f"""
<p>Les présentes conditions générales régissent l'utilisation du site et des services proposés par <strong>Kolê Group</strong> (ci-après « la Plateforme »). En accédant au site ou en créant un compte, vous acceptez ces conditions dans leur intégralité.</p>
<p><em>Dernière mise à jour : mai 2026</em></p>

<h2>1. Objet</h2>
<p>Kolê Group est une marketplace mettant en relation des acheteurs avec des vendeurs, prestataires de services et artistes basés principalement en Côte d'Ivoire et en Afrique. La Plateforme permet la consultation de catalogues, la passation de commandes, la réservation de prestations et l'achat de contenus culturels (musique, billets d'événements).</p>

<h2>2. Compte utilisateur</h2>
<ul>
  <li>L'inscription est ouverte aux personnes majeures ou aux mineurs sous responsabilité d'un représentant légal.</li>
  <li>Vous vous engagez à fournir des informations exactes et à maintenir la confidentialité de vos identifiants.</li>
  <li>Kolê Group peut suspendre ou supprimer un compte en cas de fraude, d'usage abusif ou de violation des présentes conditions.</li>
</ul>

<h2>3. Rôle de Kolê Group</h2>
<p>Sauf mention contraire, Kolê Group agit en qualité d'<strong>intermédiaire technique</strong>. Les contrats de vente ou de prestation sont conclus directement entre l'acheteur et le vendeur ou le prestataire. Kolê Group facilite la mise en relation, le paiement en ligne et le suivi des commandes lorsque ces fonctionnalités sont activées.</p>

<h2>4. Commandes et prix</h2>
<ul>
  <li>Les prix sont indiqués en francs CFA (FCFA) sauf mention contraire.</li>
  <li>Une commande n'est définitive qu'après confirmation affichée sur le site et, le cas échéant, après validation du paiement.</li>
  <li>Le vendeur reste responsable de la conformité, de la disponibilité et de la description de ses produits ou services.</li>
  <li>Les offres promotionnelles (ventes flash, codes promo) sont soumises à leurs conditions spécifiques et à des stocks limités.</li>
</ul>

<h2>5. Paiement</h2>
<p>Les paiements en ligne sont traités par notre partenaire <strong>GeniusPay</strong>. Kolê Group n'est pas responsable des interruptions temporaires du service de paiement imputables au prestataire ou aux opérateurs mobiles. En cas d'échec de paiement, la commande peut être annulée automatiquement.</p>

<h2>6. Livraison et exécution</h2>
<ul>
  <li>Les délais et frais de livraison sont indiqués avant validation ou communiqués par le vendeur.</li>
  <li>L'acheteur doit fournir une adresse et un numéro de téléphone valides.</li>
  <li>En cas de retard important, contactez d'abord le vendeur via la messagerie de commande, puis le support Kolê Group.</li>
</ul>

<h2>7. Droit de réclamation</h2>
<p>Tout problème (produit endommagé, non reçu, non conforme) doit être signalé dans un délai de <strong>7 jours</strong> après réception. Kolê Group peut intervenir en médiation entre les parties mais ne garantit pas un remboursement automatique sans examen du dossier.</p>

<h2>8. Vendeurs, prestataires et artistes</h2>
<ul>
  <li>L'ouverture d'une boutique ou d'un profil professionnel peut nécessiter un abonnement payant.</li>
  <li>Les vendeurs s'engagent à respecter la réglementation locale, la propriété intellectuelle et les règles de la Plateforme.</li>
  <li>Kolê Group se réserve le droit de retirer un catalogue ou de suspendre un compte professionnel en cas de manquement.</li>
</ul>

<h2>9. Kolê Culture</h2>
<p>L'achat de billets et de contenus musicaux est soumis aux conditions affichées sur chaque fiche événement ou titre. Les billets comportant un QR code sont personnels et non réutilisables après validation à l'entrée.</p>

<h2>10. Propriété intellectuelle</h2>
<p>Le nom Kolê Group, le logo, l'interface du site et les contenus éditoriaux de la Plateforme sont protégés. Toute reproduction non autorisée est interdite. Les vendeurs et artistes garantissent détenir les droits sur les contenus qu'ils publient.</p>

<h2>11. Données personnelles</h2>
<p>Le traitement de vos données est décrit dans notre <a href="/page/confidentialite/">politique de confidentialité</a>. En utilisant le site, vous en acceptez les principes.</p>

<h2>12. Limitation de responsabilité</h2>
<p>Kolê Group met en œuvre des moyens raisonnables pour assurer la disponibilité du service. Elle ne saurait être tenue responsable des dommages indirects, des indisponibilités liées au réseau ou des litiges strictement commerciaux entre utilisateurs, sous réserve des dispositions légales impératives applicables.</p>

<h2>13. Modification des conditions</h2>
<p>Kolê Group peut modifier les présentes conditions. La version en vigueur est celle publiée sur cette page. La poursuite de l'utilisation du site vaut acceptation des nouvelles conditions.</p>

<h2>14. Droit applicable</h2>
<p>Les présentes conditions sont régies par le droit en vigueur en <strong>Côte d'Ivoire</strong>. En cas de litige, les parties rechercheront une solution amiable avant toute action judiciaire.</p>

<h2>15. Contact</h2>
<p>Pour toute question relative à ces conditions :</p>
<ul>
  <li>E-mail : <a href="mailto:{KOLE_CONTACT_EMAIL}">{KOLE_CONTACT_EMAIL}</a></li>
  <li>Téléphone / WhatsApp : <a href="tel:{KOLE_CONTACT_PHONE_INTL}">{KOLE_CONTACT_PHONE}</a></li>
</ul>
"""


def confidentialite_content() -> str:
    return f"""
<p>La présente politique explique comment <strong>Kolê Group</strong> collecte, utilise et protège vos données personnelles lorsque vous utilisez notre site et nos services.</p>
<p><em>Dernière mise à jour : mai 2026</em></p>

<h2>1. Responsable du traitement</h2>
<p>Le responsable du traitement est <strong>Kolê Group</strong>. Pour toute demande relative à vos données :</p>
<ul>
  <li>E-mail : <a href="mailto:{KOLE_CONTACT_EMAIL}">{KOLE_CONTACT_EMAIL}</a></li>
  <li>Téléphone : <a href="tel:{KOLE_CONTACT_PHONE_INTL}">{KOLE_CONTACT_PHONE}</a></li>
</ul>

<h2>2. Données collectées</h2>
<p>Selon votre utilisation du site, nous pouvons collecter :</p>
<ul>
  <li><strong>Identité et contact :</strong> nom, prénom, adresse e-mail, numéro de téléphone, ville, adresse de livraison.</li>
  <li><strong>Compte :</strong> identifiant, mot de passe (stocké de manière sécurisée et chiffrée), photo de profil.</li>
  <li><strong>Commandes :</strong> historique d'achats, montants, statuts, messages échangés avec les vendeurs.</li>
  <li><strong>Paiement :</strong> références de transaction fournies par GeniusPay (nous ne stockons pas vos codes PIN ni numéros de carte complets).</li>
  <li><strong>Navigation :</strong> pages consultées, préférences, favoris, panier, cookies techniques.</li>
  <li><strong>Espace pro / Culture :</strong> informations de boutique, prestations, profils artiste, billets achetés.</li>
</ul>

<h2>3. Finalités</h2>
<p>Vos données sont utilisées pour :</p>
<ul>
  <li>créer et gérer votre compte ;</li>
  <li>traiter et suivre vos commandes, réservations et achats culturels ;</li>
  <li>assurer le support client et la médiation entre utilisateurs ;</li>
  <li>envoyer des notifications liées au service (confirmation, statut, sécurité du compte) ;</li>
  <li>améliorer la Plateforme et prévenir la fraude ;</li>
  <li>respecter nos obligations légales.</li>
</ul>

<h2>4. Base légale</h2>
<p>Les traitements reposent sur l'exécution du contrat (commande, compte), votre consentement lorsque requis (newsletter, cookies non essentiels), et l'intérêt légitime de Kolê Group à sécuriser et améliorer le service.</p>

<h2>5. Partage des données</h2>
<p>Vos données peuvent être communiquées :</p>
<ul>
  <li>aux <strong>vendeurs et prestataires</strong> concernés par votre commande ou demande ;</li>
  <li>à nos <strong>prestataires techniques</strong> (hébergement, paiement, envoi d'e-mails) dans la limite nécessaire à leur mission ;</li>
  <li>aux <strong>autorités</strong> si la loi l'exige.</li>
</ul>
<p>Nous ne vendons pas vos données personnelles à des tiers.</p>

<h2>6. Durée de conservation</h2>
<ul>
  <li>Compte actif : données conservées tant que le compte existe.</li>
  <li>Commandes et factures : conservation conforme aux obligations comptables et fiscales.</li>
  <li>Données de connexion et logs : durée limitée à des fins de sécurité.</li>
  <li>Compte inactif ou supprimé : suppression ou anonymisation dans un délai raisonnable, sauf obligation légale de conservation.</li>
</ul>

<h2>7. Sécurité</h2>
<p>Nous mettons en place des mesures techniques et organisationnelles adaptées : connexion sécurisée (HTTPS), mots de passe chiffrés, accès restreint aux données sensibles. Aucune transmission sur Internet n'est toutefois totalement exempte de risque.</p>

<h2>8. Cookies</h2>
<p>Le site utilise des cookies nécessaires au fonctionnement (session, panier, authentification). D'autres cookies analytiques ou de préférence peuvent être utilisés pour améliorer l'expérience. Vous pouvez configurer votre navigateur pour refuser certains cookies ; certaines fonctionnalités pourraient alors être limitées.</p>

<h2>9. Vos droits</h2>
<p>Conformément à la réglementation applicable, vous pouvez demander :</p>
<ul>
  <li>l'accès à vos données ;</li>
  <li>la rectification d'informations inexactes ;</li>
  <li>la suppression lorsque le traitement n'est plus justifié ;</li>
  <li>la limitation ou l'opposition à certains traitements ;</li>
  <li>la portabilité lorsque applicable.</li>
</ul>
<p>Adressez votre demande à <a href="mailto:{KOLE_CONTACT_EMAIL}">{KOLE_CONTACT_EMAIL}</a> en précisant l'objet et, si possible, votre identifiant de compte.</p>

<h2>10. Mineurs</h2>
<p>Le site s'adresse principalement aux personnes majeures. Si un mineur utilise la Plateforme, cela doit se faire avec l'accord d'un parent ou tuteur légal.</p>

<h2>11. Modifications</h2>
<p>Cette politique peut être mise à jour. La date de dernière révision figure en tête de page. Nous vous invitons à la consulter régulièrement.</p>
"""


STATIC_PAGES = (
    {"slug": "faq", "title": "FAQ", "content": faq_page_content},
    {"slug": "conditions-generales", "title": "Conditions générales", "content": conditions_generales_content},
    {"slug": "confidentialite", "title": "Confidentialité", "content": confidentialite_content},
    {"slug": "contact", "title": "Contact", "content": contact_page_content},
)

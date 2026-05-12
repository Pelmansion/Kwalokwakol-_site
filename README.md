# KwaloKWakolê — Plateforme e-commerce & culture

Site web **Django** pour **KwaloKWakolê Group** : marketplace (boutiques, prestataires de services), commandes, avis, messagerie, paiements (bac à sable), **abonnements** vendeurs / prestataires (montants fixés par l’admin), module **Culture** (artistes, musique, billets de concert avec QR), **PWA** (installation sur mobile) et assistant FAQ **Kwa** intégré.

## Fonctionnalités principales

- **Boutique** : catalogue, panier, favoris, commandes, vendeurs vérifiés  
- **Prestataires** : profils, demandes de service, tableau de bord  
- **Abonnements** : souscription obligatoire pour finaliser l’inscription vendeur / prestataire  
- **Culture** : profils artistes, streaming / achat de titres, événements et billets  
- **Comptes** : inscription, profils, rôles (client, vendeur, prestataire, admin)  
- **PWA** : manifeste, service worker, page hors ligne (voir `docs/PWA_ET_APPLICATION_MOBILE.md`)

## Prérequis

- **Python 3.12+** (projet testé avec Django 6.x)  
- Un environnement virtuel (`venv`) recommandé

## Installation locale

```bash
cd SITE_AIPAC_PROJET
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
copy .env.example .env          # puis éditer .env pour l’email (optionnel)
python manage.py migrate
python manage.py runserver
```

Ouvrir [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

### Données de démonstration (optionnel)

```bash
python manage.py seed_test_data
# Réinitialiser puis recharger :
python manage.py seed_test_data --reset
```

Mot de passe par défaut des comptes de test : voir la sortie de la commande (souvent `demo1234`).

## Structure du projet (aperçu)

| Dossier / app | Rôle |
|---------------|------|
| `kwalo/` | Configuration Django (`settings`, URLs racine) |
| `store/`, `catalog/` | Vitrine et produits |
| `marketplace/` | Vendeurs, prestataires, tableaux de bord |
| `subscriptions/` | Formules et paiements d’abonnement |
| `culture/` | Artistes, musique, concerts, billets |
| `accounts/`, `orders/`, `payments/`, `reviews/`, `messaging/`, `notifications/` | Comptes, commandes, paiements, avis, messages |
| `templates/`, `static/` | Interface (thème, PWA, chatbot) |
| `frontend/` | Assets React / Vite (build séparé si besoin) |

## Déploiement

Avant la mise en production : `DEBUG = False`, `SECRET_KEY` et `ALLOWED_HOSTS` sécurisés, base de données adaptée (PostgreSQL recommandé), fichiers statiques et médias servis correctement (`collectstatic`, stockage média). Consulter la [checklist Django déploiement](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/).

## Licence & contact

Projet **KwaloKWakolê Group**. Pour toute question sur le dépôt ou les contributions, ouvrir une issue sur GitHub ou contacter les mainteneurs du projet.

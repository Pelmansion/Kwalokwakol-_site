# Publier Kolê sur Google Play et sur l’App Store

Votre site est déjà une **PWA** (installable depuis le navigateur). Les **stores** demandent une **coque native** qui affiche votre site (ou une **TWA** côté Android). Vous ne réécrivez pas la boutique : vous empaquetez l’URL de production.

---

## 1. Prérequis communs

| Élément | Détail |
|--------|--------|
| **Site en HTTPS** | Obligatoire (déjà le cas en prod). |
| **URL canonique** | Une seule URL officielle (ex. `https://www.votredomaine.ci/`). |
| **Politique de confidentialité** | Page publique obligatoire pour les deux stores. |
| **Compte développeur Google** | Frais d’inscription **une fois** (montant fixé par Google). |
| **Compte Apple Developer** | **Environ 99 USD / an** pour publier sur l’App Store. |

---

## 2. Google Play (Android)

### Option A — **PWABuilder** (recommandé pour débuter)

1. Aller sur [PWABuilder](https://www.pwabuilder.com/).
2. Entrer l’URL **HTTPS** de votre site en production.
3. Vérifier le score PWA (manifest, service worker, icônes — déjà présents dans le projet).
4. Générer le paquet **« Android »** (TWA / projet Android Studio).
5. Ouvrir le projet dans **Android Studio**, configurer le **package name** (ex. `ci.kwalokwakole.app`), signer l’application avec un **keystore** que vous conservez précieusement.
6. Créer la fiche sur **Google Play Console**, remplir le questionnaire (contenu, public cible, politique de confidentialité), téléverser l’**AAB** (format exigé pour les nouvelles apps).
7. **Lier le site à l’app (TWA)** : publier le fichier **`assetlinks.json`** à l’adresse exacte  
   `https://votredomaine/.well-known/assetlinks.json`  
   Voir `docs/exemples/assetlinks.json.example` (remplacer le nom de package et les empreintes SHA-256 du certificat de signature de l’app).

### Icône d’app / APK et manifeste web

Les fichiers `static/images/icons/icon-*.png` et `apple-touch-icon.png` sont produits par **`python scripts/generate_pwa_icons.py`** et référencés par le **manifest** du site (`/manifest.webmanifest`). Chrome les utilise pour « Ajouter à l’écran d’accueil ».

**Important :** un **APK ou AAB** généré avec **PWABuilder** ou **Bubblewrap** embarque une **copie** des icônes **au moment où vous construisez le projet**. Changer le site et le script ne met pas à jour l’icône déjà installée tant que vous n’avez pas **régénéré le paquet Android** et publié une **nouvelle version** sur le Play Store (ou réinstallé un APK de test).

### Option B — **Bubblewrap** (ligne de commande)

Outil Google pour générer un projet TWA à partir de l’URL et du manifest. Nécessite Node.js. Documentation : [bubblewrap](https://github.com/GoogleChromeLabs/bubblewrap).

### Après publication

- Chaque mise à jour **du site** est visible **sans** republier l’app, sauf si vous changez le domaine, le scope ou des paramètres natifs.
- Une **nouvelle version** sur le Play Store est surtout nécessaire pour changer la coque, le certificat, ou les métadonnées Play.

---

## 3. App Store (iOS)

Apple **ne propose pas** l’équivalent officiel de la TWA Google. Les approches courantes :

### Option A — **Capacitor** (Ionic)

1. Créer un petit projet **Capacitor** avec une **WebView** en plein écran qui charge votre URL de production.
2. Configurer **ATS** (App Transport Security) pour n’autoriser que HTTPS.
3. Ajouter les **icônes** et **splash screens** aux tailles exigées par Apple.
4. Ouvrir le dossier `ios` dans **Xcode**, définir le **Bundle ID**, les certificats de signature, **Privacy Manifest** (obligatoire pour les nouvelles soumissions).
5. Soumettre via **App Store Connect** (captures d’écran iPhone, description, politique de confidentialité, etc.).

### Option B — **Cordova** / **WebView** maison

Même idée : application iOS minimale qui charge `https://votre-domaine/`. Même vigilance sur les règles Apple (voir ci-dessous).

### Règles Apple importantes

- La **directive 4.2.6** (et proches) : une app qui ne fait qu’afficher un site web sans apport « app-like » peut être **refusée** si elle est jugée trop proche d’une simple expérience Safari. En pratique, beaucoup de marques publient des **apps conteneur** en ajoutant au minimum : bonnes performances, gestion du retour arrière, éventuellement **notifications push** (UNUserNotificationCenter + service), ou **fonctions natives légères** (partage, biométrie pour se connecter, etc.).
- Prévoir une **description honnête** du rôle de l’app (« accès rapide à la marketplace Kolê »).

---

## 4. Cohérence avec votre projet Django

- **Manifest** : `https://votredomaine/manifest.webmanifest` (déjà exposé dans `kwalo/urls.py`).
- **Service worker** : `https://votredomaine/sw.js` (déjà en place).
- **Icônes** : `static/images/icons/` (192, 512, maskable, Apple touch — script `scripts/generate_pwa_icons.py` si besoin de régénérer).

Pour **Android TWA**, le fichier **`/.well-known/assetlinks.json`** doit être servi **exactement** sur le **même hôte** que celui déclaré dans l’app (souvent `www` vs sans `www` : choisir une variante et la rediriger en 301).

Sur **Render / nginx**, vous pouvez soit :

- servir un fichier statique à cet emplacement, soit  
- ajouter une **vue Django** dédiée qui renvoie le JSON (éviter les espaces / erreurs de copier-coller dans l’admin).

---

## 5. Ordre de travail suggéré

1. Finaliser le site en **production HTTPS** et tester la PWA (installation depuis Chrome Android).
2. **Play Store** : PWABuilder ou Bubblewrap → AAB → `assetlinks.json` → soumission.
3. **App Store** : projet Capacitor + Xcode → conformité confidentialité → soumission App Store Connect.
4. Prévoir du **délai** pour les revues (surtout Apple) et d’éventuels allers-retours.

Pour un accompagnement juridique (CGU, RGPD, mentions pour les achats in-app si un jour vous en avez), faites appel à un conseil adapté à la Côte d’Ivoire / à l’UE selon votre cible.

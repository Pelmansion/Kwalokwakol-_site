# 📱 Kolê — PWA & Application mobile

Ce document explique comment le site Django **KwaloKWakolê Group** est transformé
en application installable (PWA), puis comment le publier sur **Google Play Store**
et **Apple App Store**.

---

## 1. Vue d'ensemble

Nous avons choisi l'approche **PWA (Progressive Web App)** pour trois raisons :

1. ✅ **Zéro réécriture** : le site Django existant devient immédiatement une app installable
2. ✅ **Un seul code à maintenir** : les mises à jour du site se propagent automatiquement à l'app
3. ✅ **Publiable sur Play Store et App Store** via l'outil gratuit [PWABuilder](https://www.pwabuilder.com)

### Ce qui est déjà en place

| Élément | Fichier | Rôle |
|---|---|---|
| Manifest | `templates/pwa/manifest.webmanifest` | Nom, icônes, couleurs, raccourcis |
| Service Worker | `templates/pwa/sw.js` | Cache offline, stratégies réseau |
| Page hors-ligne | `templates/pwa/offline.html` | Page élégante quand pas de réseau |
| Icônes | `static/images/icons/` | 192, 512, maskable, apple-touch |
| Meta tags PWA | `templates/base.html` | Intégration iOS, Android, Windows |
| Bouton d'installation | `base.html` (`#pwa-install-btn`) | Propose à l'utilisateur d'installer |
| Routes Django | `kwalo/urls.py` | `/manifest.webmanifest`, `/sw.js`, `/hors-ligne/` |

### Régénération des icônes

Si vous changez le logo principal, relancez :

```bash
python scripts/generate_pwa_icons.py
```

---

## 2. Tester la PWA en local

1. **Lancer le serveur** :
   ```bash
   python manage.py runserver
   ```

2. **Ouvrir Chrome** sur `http://localhost:8000/`

3. **Vérifier avec Lighthouse** :
   - Ouvrir les DevTools (F12)
   - Onglet **Lighthouse** → cocher **Progressive Web App**
   - Cliquer sur **Analyze page load**
   - Vous devez voir le badge "Installable" ✅

4. **Installer l'app** :
   - Un petit bouton **"📲 Installer l'app"** apparaît en bas à droite
   - Cliquer dessus → l'app s'installe comme n'importe quelle app desktop/mobile

> ⚠️ En production, le site **DOIT être servi en HTTPS** pour que le service worker
> fonctionne. Sur `localhost` c'est exempté, mais pour Play Store / App Store,
> un certificat SSL valide est obligatoire.

---

## 3. Publication sur Google Play Store

### Prérequis

- Votre site est déployé et accessible en **HTTPS** (ex : `https://kwalok.ci`)
- Un compte **Google Play Console** (frais unique : **25 USD**)
  → [play.google.com/console](https://play.google.com/console/signup)

### Étapes avec PWABuilder (recommandé)

1. Aller sur **[www.pwabuilder.com](https://www.pwabuilder.com/)**

2. Entrer votre URL de production (ex : `https://kwalok.ci`)
   - PWABuilder analyse votre site et vérifie la PWA
   - Score attendu : **≥ 90/100**

3. Cliquer sur **"Package for stores"** puis choisir **Android**

4. Remplir les informations :
   - **Package ID** : `ci.kwalok.app` (ou similaire, inverse-domaine)
   - **App name** : `KwaloKWakolê Group`
   - **Short name** : `Kolê`
   - **Version** : `1.0.0`
   - **Launcher name** : `Kolê`
   - **Theme color** : `#C2410C`
   - **Background color** : `#FFF8F1`
   - **Signing key** : laisser **"Generate new"** la première fois
     (⚠️ **TÉLÉCHARGER et CONSERVER** le fichier `.keystore` généré — il est
     indispensable pour toute mise à jour future de l'app sur Play Store)

5. Cliquer sur **"Generate"** → téléchargement d'un `.zip` contenant :
   - `app-release-bundle.aab` ← **le fichier à uploader sur Play Store**
   - `app-release-signed.apk` ← pour tests locaux
   - `signing.keystore` + `signing-key-info.txt` ← **à sauvegarder précieusement**

### Vérifier le Digital Asset Links

Pour que l'app Android reconnaisse votre site et masque la barre d'URL (Trusted
Web Activity), il faut publier un fichier `/.well-known/assetlinks.json` sur
votre domaine.

Le fichier exact est fourni dans le zip PWABuilder (`assetlinks.json`). À placer à :

```
https://kwalok.ci/.well-known/assetlinks.json
```

**Intégration Django** (à ajouter une fois le domaine connu) :

```python
# kwalo/urls.py
from django.views.generic import TemplateView

urlpatterns = [
    ...,
    path(
        '.well-known/assetlinks.json',
        TemplateView.as_view(
            template_name='pwa/assetlinks.json',
            content_type='application/json',
        ),
    ),
]
```

Et créer `templates/pwa/assetlinks.json` avec le contenu fourni par PWABuilder.

### Upload sur Play Console

1. Se connecter à **[play.google.com/console](https://play.google.com/console)**
2. Créer une nouvelle **application**
3. Dans **Production** → **Créer une version**
4. Uploader le fichier **`app-release-bundle.aab`**
5. Remplir les fiches (description, captures, catégorie "Shopping", etc.)
6. Soumettre pour examen — validation sous **2 à 5 jours** en moyenne

---

## 4. Publication sur Apple App Store

### Prérequis

- Site en HTTPS
- Un **Mac** (indispensable pour builder sous Xcode) — ou utiliser un service
  cloud comme **[Codemagic](https://codemagic.io)** ou **[MacStadium](https://macstadium.com)**
- Un compte **Apple Developer Program** (**99 USD/an**)
  → [developer.apple.com/programs](https://developer.apple.com/programs/)

### Étapes avec PWABuilder

1. Sur **pwabuilder.com**, après l'analyse, cliquer **"Package for stores"** → **iOS**

2. Remplir :
   - **Bundle ID** : `ci.kwalok.app`
   - **App name** : `Kolê`
   - **Image URL** : URL de l'icône 512x512 hébergée en HTTPS

3. Télécharger le zip → contient un **projet Xcode complet**

4. Sur un Mac :
   - Ouvrir `App.xcworkspace` dans **Xcode**
   - Dans **Signing & Capabilities**, sélectionner votre Team (compte Apple Dev)
   - **Product** → **Archive**
   - Dans la fenêtre Organizer, cliquer **Distribute App** → **App Store Connect**

5. Sur **[appstoreconnect.apple.com](https://appstoreconnect.apple.com)** :
   - Créer la fiche app (description, mots-clés, captures iPhone/iPad...)
   - Soumettre à la review — validation sous **24 à 48h** en général

> ⚠️ **Attention** : Apple a des règles plus strictes. Votre app doit apporter
> une valeur au-delà d'un simple site web emballé. Le fait d'avoir un véritable
> marketplace avec transactions, comptes utilisateurs, notifications, etc.
> rend l'acceptation plus facile.

---

## 5. Checklist avant publication

### Technique

- [ ] Site déployé en **HTTPS** avec certificat valide
- [ ] `ALLOWED_HOSTS` contient le domaine de production
- [ ] Service worker `/sw.js` renvoie 200 avec `Content-Type: application/javascript`
- [ ] Manifest `/manifest.webmanifest` renvoie 200
- [ ] Lighthouse PWA score ≥ 90
- [ ] Test d'installation sur Chrome mobile réel (Android)
- [ ] Test d'installation sur Safari iOS (Ajouter à l'écran d'accueil)
- [ ] `assetlinks.json` publié pour Android (après génération via PWABuilder)

### Contenu (obligatoire pour les stores)

- [ ] Icône 512x512 PNG
- [ ] Icône 1024x1024 PNG (App Store)
- [ ] Bannière marketing 1024x500 (Play Store)
- [ ] **Au moins 2 captures d'écran** par format (téléphone, tablette)
- [ ] **Description courte** (80 caractères max)
- [ ] **Description longue** (4000 caractères max)
- [ ] **Catégorie** : Shopping / Commerce
- [ ] **Classification de contenu** (questionnaire Play Store / App Store)
- [ ] **Politique de confidentialité** en ligne (URL requise)
- [ ] **Conditions d'utilisation** en ligne
- [ ] **Email de contact** support

### Légal

- [ ] Mentions légales (société, SIRET/RCCM, adresse...)
- [ ] RGPD / protection données (même hors UE c'est une bonne pratique)
- [ ] Conditions de vente pour les transactions e-commerce

---

## 6. Après publication : mises à jour

La force de la PWA : **les mises à jour du site sont automatiques**.

Quand vous poussez un changement sur le serveur Django :
1. L'utilisateur ouvre l'app
2. Le service worker détecte une nouvelle version
3. Le toast « Une nouvelle version est disponible » apparaît
4. L'utilisateur clique sur **Actualiser** → il a la dernière version

**Pas besoin de repasser par Play Store / App Store** pour les modifications
de contenu, produits, design, etc.

Il faudra uniquement refaire un upload si vous changez :
- L'icône principale
- Le nom de l'app
- Les permissions natives demandées
- Les paramètres fondamentaux du manifest

### Versionner les mises à jour du cache

Dans `templates/pwa/sw.js`, incrémentez la constante au début du fichier :

```js
const VERSION = 'kwalok-v1';  // passer à 'kwalo-v2', 'v3', etc.
```

Cela force le service worker à invalider l'ancien cache et à recharger tous
les fichiers statiques.

---

## 7. Ressources utiles

- 🛠 [PWABuilder](https://www.pwabuilder.com) — générateur Play Store / App Store
- 📐 [Lighthouse](https://developers.google.com/web/tools/lighthouse) — audit PWA
- 📘 [Google Play Console](https://play.google.com/console)
- 🍏 [App Store Connect](https://appstoreconnect.apple.com)
- 📖 [Bubblewrap](https://github.com/GoogleChromeLabs/bubblewrap) — alternative CLI Google pour Android
- 📚 [Doc PWA MDN](https://developer.mozilla.org/fr/docs/Web/Progressive_web_apps)

---

## 8. Coûts récapitulatifs

| Plateforme | Frais unique | Frais annuel |
|---|---|---|
| PWA (auto-hébergée) | 0 € | Coût du domaine + hébergement |
| Google Play Store | 25 USD | 0 |
| Apple App Store | 0 | **99 USD/an** |

**Total pour publier partout** : ~25 USD + 99 USD/an

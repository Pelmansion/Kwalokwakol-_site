/* ============================================================
 * Kolê Chatbot "Kwa"
 * FAQ intelligent par mots-clés, navigation guidée.
 * Aucune dépendance externe, fonctionne hors ligne.
 * ============================================================ */
(function () {
  "use strict";

  // ----- Récupère les URLs depuis l'attribut data du root -----
  const root = document.getElementById("kwalo-chatbot");
  if (!root) return;

  const urls = JSON.parse(root.dataset.urls || "{}");
  const isAuthenticated = root.dataset.authenticated === "1";

  // ----- Helpers de normalisation (accents, ponctuation) -----
  function normalize(text) {
    return (text || "")
      .toString()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  // ----- Quick replies réutilisables -----
  const QR = {
    home: { label: "🏠 Accueil", url: urls.home },
    products: { label: "🛍 Catalogue produits", url: urls.products },
    cart: { label: "🛒 Mon panier", url: urls.cart },
    favorites: { label: "❤️ Mes favoris", url: urls.favorites },
    cultureHome: { label: "🎤 Kolê Culture", url: urls.culture },
    songList: { label: "🎵 Catalogue musique", url: urls.songs },
    eventList: { label: "🎫 Concerts", url: urls.events },
    artistList: { label: "🌟 Artistes", url: urls.artists },
    becomeVendor: { label: "🏪 Devenir vendeur", url: urls.becomeVendor },
    becomeProvider: { label: "🛠 Devenir prestataire", url: urls.becomeProvider },
    becomeArtist: { label: "🎤 Devenir artiste", url: urls.becomeArtist },
    plans: { label: "💳 Voir les formules", url: urls.plans },
    login: { label: "🔑 Se connecter", url: urls.login },
    signup: { label: "📝 Créer un compte", url: urls.signup },
    contact: { label: "📞 Contact", url: urls.contact },
    faq: { label: "❓ FAQ complète", url: urls.faq },
    myOrders: { label: "📦 Mes commandes", url: urls.orders },
    myTickets: { label: "🎫 Mes billets", url: urls.myTickets },
    myPurchases: { label: "🎵 Mes achats musique", url: urls.myPurchases },
  };

  // ----- Suggestions par défaut (1er message) -----
  const WELCOME_QR = ["products", "cultureHome", "becomeVendor", "becomeArtist"];
  const FALLBACK_QR = ["products", "cultureHome", "becomeVendor", "contact"];

  // ----- Base de connaissance -----
  // Chaque intent : patterns (regex ou mots-clés), réponse, quickReplies
  const intents = [
    {
      id: "greeting",
      patterns: [
        "bonjour", "salut", "bonsoir", "hello", "hi", "coucou", "yo", "hey",
        "comment ca va", "ca va", "wesh"
      ],
      response: "Bonjour ! 👋 Je suis **Kwa**, l'assistant de KwaloKWakolê Group. Je peux t'aider à acheter, vendre, écouter de la musique ou réserver tes places de concert. Que cherches-tu ?",
      quickReplies: WELCOME_QR,
    },

    // ===== Produits & shopping =====
    {
      id: "shopping_general",
      patterns: ["produit", "acheter", "boutique", "shopping", "magasin", "article", "vendre", "commande", "commander"],
      response: "🛍 Tu peux parcourir notre **catalogue de produits** locaux : alimentation, artisanat, bâtiment, mode... Filtre par catégorie, ville ou prix. Ajoute au panier puis passe ta commande.",
      quickReplies: ["products", "cart", "favorites"],
    },
    {
      id: "delivery",
      patterns: ["livraison", "livrer", "expedition", "delai", "combien de temps", "quand recevoir", "deliver"],
      response: "🚚 **Livraison** :\n• Gratuite dès **15 000 FCFA** d'achat\n• Délai habituel : 24h en zone urbaine, 2-3 jours en zone rurale\n• Suivi disponible dans tes commandes\n• Paiement à la livraison possible selon le vendeur",
      quickReplies: ["myOrders", "products"],
    },
    {
      id: "payment",
      patterns: ["paiement", "payer", "wave", "orange money", "moov", "mtn", "carte bancaire", "espece", "comment payer", "moyens"],
      response: "💳 **Moyens de paiement** :\n• **GeniusPay** (Wave, Orange Money, MTN MoMo, carte bancaire…) pour le paiement en ligne sur la boutique et les services payants\n• **Espèces à la livraison** quand c’est proposé sur la commande\n\nLes encaissements en ligne passent par GeniusPay ; tu reçois une confirmation par email.",
      quickReplies: ["cart", "contact"],
    },
    {
      id: "return_refund",
      patterns: ["retour", "rembours", "annul", "echange", "produit defectueux", "casse", "abime"],
      response: "↩️ **Retours & remboursements** :\n• Tu disposes de **7 jours** après réception pour signaler un problème\n• Contacte le vendeur via la messagerie de la commande\n• En cas de litige, l'équipe Kolê arbitre\n• Remboursement sur le moyen de paiement initial",
      quickReplies: ["myOrders", "contact"],
    },
    {
      id: "track_order",
      patterns: ["suivre", "suivi", "ou est ma commande", "statut commande", "tracking", "ma commande"],
      response: "📦 Pour **suivre ta commande**, va dans **Mon profil → Mes commandes**. Chaque commande a un statut : En préparation → Expédiée → Livrée. Tu reçois aussi des notifications par email.",
      quickReplies: ["myOrders", "contact"],
    },
    {
      id: "favorites",
      patterns: ["favori", "favoris", "wishlist", "liste de souhait", "preferer"],
      response: "❤️ Ajoute des produits à tes **favoris** en cliquant sur le cœur sur n'importe quel article. Tu les retrouves ensuite dans le menu Compte → Mes favoris.",
      quickReplies: ["favorites", "products"],
    },

    // ===== Vendeur / Prestataire =====
    {
      id: "become_vendor",
      patterns: ["devenir vendeur", "vendre mes produits", "ouvrir une boutique", "vendre sur kwalok", "creer une boutique", "boutique en ligne"],
      response: "🏪 **Devenir vendeur** sur Kolê :\n1. Crée ton compte\n2. Remplis ton profil boutique (nom, KYC, photos)\n3. Souscris à une formule mensuelle (Starter / Pro / Premium)\n4. Publie tes produits → c'est en ligne !\n\nLes vendeurs vérifiés bénéficient d'un badge de confiance.",
      quickReplies: ["becomeVendor", "plans"],
    },
    {
      id: "become_provider",
      patterns: ["devenir prestataire", "vendre mes services", "proposer mes services", "freelance", "service", "prestation"],
      response: "🛠 **Devenir prestataire de services** :\nCoiffure, plomberie, bâtiment, couture, numérique... Tu peux proposer tes services sur Kolê.\n1. Inscription + KYC\n2. Choix d'une formule mensuelle\n3. Publication de tes services → réception de demandes",
      quickReplies: ["becomeProvider", "plans"],
    },
    {
      id: "kyc",
      patterns: ["kyc", "verifier identite", "piece identite", "document", "verification", "verified"],
      response: "🔐 **Vérification KYC** : Pour devenir vendeur ou prestataire, tu dois fournir une pièce d'identité (recto/verso) et une photo. Cela protège les acheteurs et te donne le badge ✓ Vérifié. La validation prend 24-48h.",
      quickReplies: ["becomeVendor", "becomeProvider"],
    },
    {
      id: "subscription",
      patterns: ["abonnement", "formule", "tarif vendeur", "prix mensuel", "starter", "pro premium", "subscription", "combien coute"],
      response: "💳 **Formules d'abonnement** vendeurs/prestataires :\n• **Starter** : pour démarrer\n• **Pro** : visibilité accrue\n• **Premium** : mise en avant + outils marketing\n\nL'admin fixe le montant exact en fonction de ton profil. Paiement mensuel sécurisé.",
      quickReplies: ["plans", "becomeVendor"],
    },
    {
      id: "vendor_dashboard",
      patterns: ["espace vendeur", "tableau de bord", "dashboard", "gerer mes produits", "ajouter produit"],
      response: "📊 Une fois vendeur, tu accèdes à ton **Espace vendeur** : gestion produits, commandes reçues, messagerie clients, statistiques de vente, paramètres boutique.",
      quickReplies: ["becomeVendor"],
    },

    // ===== Culture (artistes, musique, concerts) =====
    {
      id: "culture_overview",
      patterns: ["kwalok culture", "culture", "musique concert", "espace culturel"],
      response: "🎤 **Kolê Culture** réunit les artistes locaux, leur musique et leurs concerts. Écoute & télécharge des sons, achète des billets avec QR code, soutiens les talents de ta région !",
      quickReplies: ["cultureHome", "songList", "eventList", "artistList"],
    },
    {
      id: "music",
      patterns: ["musique", "chanson", "son", "ecouter", "ecoute", "telecharger chanson", "mp3", "album", "single", "stream"],
      response: "🎵 **Catalogue musique** : streaming gratuit pour la plupart des sons. Téléchargement libre ou payant selon le choix de l'artiste. Filtres par genre (Coupé-décalé, Zouglou, Reggae, Afrobeat...).",
      quickReplies: ["songList", "artistList", "myPurchases"],
    },
    {
      id: "artist",
      patterns: ["artiste", "chanteur", "rappeur", "musicien", "groupe", "interpret"],
      response: "🌟 Découvre les **artistes locaux** : bio, discographie, concerts à venir, réseaux sociaux. Chaque artiste a une page dédiée avec tous ses sons.",
      quickReplies: ["artistList", "songList", "becomeArtist"],
    },
    {
      id: "become_artist",
      patterns: ["devenir artiste", "publier ma musique", "mettre ma musique", "uploader chanson", "etre artiste"],
      response: "🎤 **Devenir artiste sur Kolê Culture** : il faut être déjà vendeur ou prestataire inscrit. Active ensuite ton profil artiste pour publier tes sons (gratuits ou payants), créer tes concerts et vendre tes billets.",
      quickReplies: ["becomeArtist", "becomeVendor", "becomeProvider"],
    },
    {
      id: "concert",
      patterns: ["concert", "spectacle", "billet", "ticket", "place concert", "evenement", "event", "live", "show"],
      response: "🎫 **Concerts à venir** : choisis ta catégorie (Standard / VIP / Carré Or), paye en ligne, reçois ton billet électronique avec QR code. Présente-le à l'entrée, le contrôleur scanne et tu rentres !",
      quickReplies: ["eventList", "myTickets"],
    },
    {
      id: "qr_ticket",
      patterns: ["qr code", "qr", "scanner billet", "comment marche billet", "validation billet", "controleur"],
      response: "📱 **Comment fonctionne le billet QR ?**\n1. Tu achètes en ligne → reçois ton billet\n2. Tu peux l'imprimer ou le garder sur ton téléphone\n3. À l'entrée, le contrôleur scanne le QR avec n'importe quelle app\n4. Le billet devient \"Utilisé\" → impossible de le réutiliser",
      quickReplies: ["eventList", "myTickets"],
    },
    {
      id: "music_download",
      patterns: ["telecharger", "download", "recuperer chanson", "garder chanson", "telechargement"],
      response: "⬇ **Téléchargement de musique** :\n• Si la chanson est **gratuite** → télécharge librement\n• Si elle est **payante** → achète, paye, puis télécharge depuis \"Mes achats musique\"\n• Le téléchargement reste accessible à vie depuis ton compte",
      quickReplies: ["songList", "myPurchases"],
    },

    // ===== Compte =====
    {
      id: "account_create",
      patterns: ["inscription", "creer compte", "s inscrire", "register", "signup", "ouvrir compte", "nouveau compte"],
      response: "📝 **Créer un compte** est gratuit : email + mot de passe et tu peux acheter, vendre, suivre tes commandes. Tu peux aussi t'inscrire avec Google ou Facebook en un clic.",
      quickReplies: ["signup", "login"],
    },
    {
      id: "account_login",
      patterns: ["connexion", "se connecter", "login", "log in", "j arrive pas a entrer", "acceder mon compte"],
      response: "🔑 Connecte-toi avec ton **email** et ton **mot de passe**, ou avec ton compte Google/Facebook.",
      quickReplies: ["login", "signup"],
    },
    {
      id: "password_forgot",
      patterns: ["mot de passe oublie", "reinitialiser", "perdu mot de passe", "forgot password", "reset password", "changer mot passe"],
      response: "🔓 **Mot de passe oublié ?** Sur la page de connexion, clique sur \"Mot de passe oublié\". Un lien sécurisé t'est envoyé par email pour le réinitialiser.",
      quickReplies: ["login"],
    },
    {
      id: "account_delete",
      patterns: ["supprimer compte", "fermer compte", "desinscrire", "quitter", "delete account"],
      response: "🗑 Pour **supprimer ton compte**, contacte le support. Note que tes commandes en cours doivent d'abord être terminées.",
      quickReplies: ["contact"],
    },

    // ===== App / PWA =====
    {
      id: "pwa_install",
      patterns: ["installer", "application", "app", "telephone", "android", "iphone", "play store", "app store", "telecharger app"],
      response: "📱 **Installer Kolê comme une app** :\n• Sur Android : un bouton \"Installer l'app\" apparaît automatiquement\n• Sur iPhone (Safari) : Partager → Sur l'écran d'accueil\n• L'app fonctionne même hors ligne pour les pages déjà visitées !",
      quickReplies: ["faq"],
    },

    // ===== Aide générale =====
    {
      id: "help",
      patterns: ["aide", "help", "support", "assistance", "j ai besoin", "probleme", "souci", "bug"],
      response: "❓ **Comment puis-je t'aider ?** Voici les sujets les plus demandés :",
      quickReplies: ["products", "cultureHome", "becomeVendor", "myOrders", "contact"],
    },
    {
      id: "human",
      patterns: ["humain", "vrai personne", "agent", "operateur", "parler a quelqu un", "support humain", "appeler"],
      response: "👤 Tu peux **contacter l'équipe Kolê** via la page Contact, par email ou WhatsApp. Pour une commande spécifique, utilise la messagerie de la commande pour parler directement au vendeur.",
      quickReplies: ["contact"],
    },
    {
      id: "contact",
      patterns: ["contact", "joindre", "email", "telephone", "numero", "whatsapp", "adresse"],
      response: "📞 Retrouve toutes nos coordonnées sur la **page Contact** : email, téléphone, WhatsApp, et nos horaires de support.",
      quickReplies: ["contact", "faq"],
    },
    {
      id: "thanks",
      patterns: ["merci", "thanks", "thank you", "gracias", "cool", "super", "parfait", "genial"],
      response: "Avec plaisir ! 😊 N'hésite pas si tu as d'autres questions.",
      quickReplies: WELCOME_QR,
    },
    {
      id: "bye",
      patterns: ["au revoir", "bye", "ciao", "a plus", "salut bye", "tchao", "bonne journee", "bonne soiree"],
      response: "À bientôt sur Kolê ! 👋 Bonne navigation.",
      quickReplies: [],
    },
    {
      id: "who",
      patterns: ["qui es tu", "qui es-tu", "tu es qui", "ton nom", "kwa qui", "comment tu t appelles"],
      response: "Je suis **Kwa**, l'assistant virtuel de KwaloKWakolê Group 🦊. Je connais bien le site et je peux t'orienter. Mais je ne suis pas un humain — pour des questions complexes, contacte l'équipe support.",
      quickReplies: ["help", "contact"],
    },
    {
      id: "what_is_kwalok",
      patterns: [
        "kwalok c est quoi", "que fait kwalok", "presentation",
        "marketplace ivoirien", "qu est ce que kwalok", "wakole"
      ],
      response: "🌍 **KwaloKWakolê Group** est une marketplace afro-moderne qui réunit en un seul endroit : alimentation locale, artisans, bâtiment, services, boutiques, et la culture (musique + concerts) de Côte d'Ivoire.",
      quickReplies: ["products", "cultureHome", "becomeVendor"],
    },
  ];

  // ----- Moteur de matching -----
  function findIntent(text) {
    const norm = normalize(text);
    if (!norm) return null;

    let best = null;
    let bestScore = 0;

    intents.forEach((intent) => {
      let score = 0;
      intent.patterns.forEach((pattern) => {
        const np = normalize(pattern);
        if (!np) return;
        if (norm === np) score += 10;
        else if (norm.includes(np)) {
          // Bonus selon longueur du pattern (plus précis = mieux)
          score += np.split(" ").length * 2 + 1;
        }
      });
      if (score > bestScore) {
        bestScore = score;
        best = intent;
      }
    });

    return bestScore >= 1 ? best : null;
  }

  // ----- État de la conversation -----
  const STORAGE_KEY = "kwalok_chatbot_history";
  let history = [];
  try {
    history = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch (_) {
    history = [];
  }

  function saveHistory() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(-50))); } catch (_) {}
  }

  function clearHistory() {
    history = [];
    saveHistory();
  }

  // ----- Rendu UI -----
  const elBubble = document.getElementById("kwalo-chatbot-bubble");
  const elPanel = document.getElementById("kwalo-chatbot-panel");
  const elClose = document.getElementById("kwalo-chatbot-close");
  const elClear = document.getElementById("kwalo-chatbot-clear");
  const elMessages = document.getElementById("kwalo-chatbot-messages");
  const elForm = document.getElementById("kwalo-chatbot-form");
  const elInput = document.getElementById("kwalo-chatbot-input");
  const elBadge = document.getElementById("kwalo-chatbot-badge");

  function open() {
    elPanel.classList.add("is-open");
    elBubble.classList.add("is-active");
    elBadge.hidden = true;
    setTimeout(() => elInput.focus(), 250);
    if (history.length === 0) sendBotMessage(intents.find((i) => i.id === "greeting"));
    scrollDown();
  }
  function close() {
    elPanel.classList.remove("is-open");
    elBubble.classList.remove("is-active");
  }
  function toggle() { elPanel.classList.contains("is-open") ? close() : open(); }

  function scrollDown() {
    requestAnimationFrame(() => {
      elMessages.scrollTop = elMessages.scrollHeight;
    });
  }

  function escapeHtml(s) {
    return s
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // **bold** + simple line breaks
  function formatMessage(text) {
    let safe = escapeHtml(text);
    safe = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    safe = safe.replace(/\n/g, "<br>");
    return safe;
  }

  function appendUser(text) {
    history.push({ role: "user", text, ts: Date.now() });
    saveHistory();
    const div = document.createElement("div");
    div.className = "kwa-msg kwa-msg--user";
    div.innerHTML = `<div class="kwa-msg__bubble">${formatMessage(text)}</div>`;
    elMessages.appendChild(div);
    scrollDown();
  }

  function appendBot(text, quickReplies) {
    history.push({ role: "bot", text, quickReplies: quickReplies || [], ts: Date.now() });
    saveHistory();

    const div = document.createElement("div");
    div.className = "kwa-msg kwa-msg--bot";
    div.innerHTML = `
      <div class="kwa-msg__avatar" aria-hidden="true">K</div>
      <div class="kwa-msg__group">
        <div class="kwa-msg__bubble">${formatMessage(text)}</div>
        ${quickReplies && quickReplies.length ? `
          <div class="kwa-quick-replies">
            ${quickReplies.map((id) => {
              const q = QR[id];
              if (!q || !q.url) return "";
              return `<a class="kwa-quick-reply" href="${q.url}">${q.label}</a>`;
            }).join("")}
          </div>
        ` : ""}
      </div>
    `;
    elMessages.appendChild(div);
    scrollDown();
  }

  function appendTyping() {
    const div = document.createElement("div");
    div.className = "kwa-msg kwa-msg--bot kwa-typing";
    div.id = "kwa-typing-indicator";
    div.innerHTML = `
      <div class="kwa-msg__avatar" aria-hidden="true">K</div>
      <div class="kwa-msg__bubble"><span></span><span></span><span></span></div>
    `;
    elMessages.appendChild(div);
    scrollDown();
  }
  function removeTyping() {
    const el = document.getElementById("kwa-typing-indicator");
    if (el) el.remove();
  }

  function sendBotMessage(intent) {
    appendTyping();
    const delay = 350 + Math.min(intent.response.length * 6, 1100);
    setTimeout(() => {
      removeTyping();
      appendBot(intent.response, intent.quickReplies || []);
    }, delay);
  }

  function handleUserInput(text) {
    text = text.trim();
    if (!text) return;
    appendUser(text);

    const intent = findIntent(text);
    if (intent) {
      sendBotMessage(intent);
    } else {
      appendTyping();
      setTimeout(() => {
        removeTyping();
        appendBot(
          "Hmm, je n'ai pas bien compris 🤔. Voici quelques sujets que je connais bien :",
          FALLBACK_QR
        );
      }, 600);
    }
  }

  // ----- Restauration depuis localStorage -----
  function restoreHistory() {
    history.forEach((entry) => {
      if (entry.role === "user") {
        const div = document.createElement("div");
        div.className = "kwa-msg kwa-msg--user";
        div.innerHTML = `<div class="kwa-msg__bubble">${formatMessage(entry.text)}</div>`;
        elMessages.appendChild(div);
      } else {
        const div = document.createElement("div");
        div.className = "kwa-msg kwa-msg--bot";
        const qr = (entry.quickReplies || []).map((id) => {
          const q = QR[id];
          if (!q || !q.url) return "";
          return `<a class="kwa-quick-reply" href="${q.url}">${q.label}</a>`;
        }).join("");
        div.innerHTML = `
          <div class="kwa-msg__avatar" aria-hidden="true">K</div>
          <div class="kwa-msg__group">
            <div class="kwa-msg__bubble">${formatMessage(entry.text)}</div>
            ${qr ? `<div class="kwa-quick-replies">${qr}</div>` : ""}
          </div>
        `;
        elMessages.appendChild(div);
      }
    });
    scrollDown();
  }

  // ----- Bind events -----
  elBubble.addEventListener("click", toggle);
  elClose.addEventListener("click", close);
  elClear.addEventListener("click", () => {
    if (!confirm("Effacer la conversation ?")) return;
    elMessages.innerHTML = "";
    clearHistory();
    sendBotMessage(intents.find((i) => i.id === "greeting"));
  });

  elForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = elInput.value;
    elInput.value = "";
    handleUserInput(text);
  });

  // Échappe ESC pour fermer
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && elPanel.classList.contains("is-open")) close();
  });

  // Restaure ou affiche le badge de notification
  if (history.length > 0) {
    restoreHistory();
  } else {
    // Petit badge pour attirer l'œil au 1er chargement
    setTimeout(() => { elBadge.hidden = false; }, 3500);
  }
})();

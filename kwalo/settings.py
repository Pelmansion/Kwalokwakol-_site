import os
import sys
from pathlib import Path

import django
import dj_database_url
from decouple import config
from django.core.exceptions import ImproperlyConfigured

from kwalo.media_storage import configure_media

# Templates des widgets Django (text.html, select.html…) requis par FORM_RENDERER TemplatesSetting
DJANGO_FORMS_TEMPLATES_DIR = Path(django.__file__).resolve().parent / "forms" / "templates"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- CHARGEMENT DES VARIABLES D'ENVIRONNEMENT ---
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    with open(_env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

# --- CONFIGURATION DE SÉCURITÉ ---
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-_9@-j=piy=kt$@j0$nu_g0k&r2*-_(w!5o=w&v!bu)qs=3_c*2')

# DEBUG est False par défaut en production
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# CORRECTION ALLOWED_HOSTS : Ajout de '*' temporaire pour s'assurer que le domaine de test Render ne bloque pas l'accès
ALLOWED_HOSTS = [
    'xn--kolgroup-m1a.com',
    'www.xn--kolgroup-m1a.com',
    'kolêgroup.com',
    'www.kolêgroup.com',
    '*', 
]
_render_host = (os.environ.get('RENDER_EXTERNAL_HOSTNAME') or '').strip()
if _render_host:
    ALLOWED_HOSTS.append(_render_host)
_extra_hosts = (os.environ.get('ALLOWED_HOSTS') or '').strip()
if _extra_hosts:
    for _h in _extra_hosts.split(','):
        _h = _h.strip()
        if _h and _h not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(_h)
if DEBUG:
    ALLOWED_HOSTS += ['localhost', '127.0.0.1', '[::1]']

# Requis derrière HTTPS (connexion / formulaires) — évite les refus CSRF en production
_local_csrf_hosts = frozenset({"localhost", "127.0.0.1", "[::1]"})
CSRF_TRUSTED_ORIGINS = []
for _h in ALLOWED_HOSTS:
    if _h == '*':
        continue
    if _h in _local_csrf_hosts:
        CSRF_TRUSTED_ORIGINS.extend((f"http://{_h}:8000", f"http://{_h}"))
    else:
        CSRF_TRUSTED_ORIGINS.append(f"https://{_h}")

# Origines supplémentaires (domaine Render, préprod, autre TLD…) — CSV dans l’environnement :
_extra_csrf = (os.environ.get("CSRF_TRUSTED_ORIGINS") or "").strip()
if _extra_csrf:
    for _raw in _extra_csrf.split(","):
        _o = _raw.strip().rstrip("/")
        if not _o:
            continue
        if not (_o.startswith("http://") or _o.startswith("https://")):
            _o = f"https://{_o}"
        CSRF_TRUSTED_ORIGINS.append(_o)
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CSRF_TRUSTED_ORIGINS))

# Cookie CSRF lisible par le JS (getCookie / fetch) — ne pas passer à HttpOnly
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# --- APPLICATIONS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    # Vos Apps
    'accounts',
    'catalog',
    'marketplace',
    'orders',
    'reviews',
    'messaging',
    'notifications',
    'payments',
    'content',
    'store',
    'subscriptions',
    'culture',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kwalo.urls'

# Widgets personnalisés (culture) + widgets Django (text.html, select.html…)
FORM_RENDERER = "kwalo.form_renderers.KwaloFormRenderer"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates', DJANGO_FORMS_TEMPLATES_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.category_nav',
                'accounts.context_processors.user_profile',
            ],
        },
    },
]

WSGI_APPLICATION = 'kwalo.wsgi.application'

# --- DATABASE ---
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default="postgresql://kwalokwakole_user:YpgKxzLHXcvFoqY5PWRzIcDLFtxaprSa@dpg-d80rc7gg4nts738ts4i0-a.oregon-postgres.render.com/kwalokwakole"),
        conn_max_age=600,
        ssl_require=True,
    )
}

# --- STATICS & MEDIA ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

_staticfiles_backend = (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
    if DEBUG
    else "whitenoise.storage.CompressedStaticFilesStorage"
)

_media = configure_media(
    base_dir=BASE_DIR,
    debug=DEBUG,
    installed_apps=INSTALLED_APPS,
)

# --- CORRECTION FINALE POUR CLOUDFLARE R2 (LECTURE & ÉCRITURE) ---
if not DEBUG and _media["USE_CLOUD_MEDIA"]:
    # 1. On définit le domaine public pour la lecture dans le navigateur
    AWS_S3_CUSTOM_DOMAIN = 'pub-8bba0406ebc941029e3fd22bfb86bd2a.r2.dev'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    
    # 2. On s'assure que le dictionnaire OPTIONS existe dans ton backend de stockage
    if "STORAGES_DEFAULT" in _media:
        if "OPTIONS" not in _media["STORAGES_DEFAULT"]:
            _media["STORAGES_DEFAULT"]["OPTIONS"] = {}
        
        # Force le domaine personnalisé pour l'affichage des images
        _media["STORAGES_DEFAULT"]["OPTIONS"]["custom_domain"] = AWS_S3_CUSTOM_DOMAIN
        
        #DÉSACTIVE la signature des URL (Indispensable pour éviter l'erreur d'enregistrement sur R2)
        _media["STORAGES_DEFAULT"]["OPTIONS"]["querystring_auth"] = False
        
        # Force l'adresse d'écriture (Vérifie que ton point de terminaison S3 y est bien)
        _media["STORAGES_DEFAULT"]["OPTIONS"]["endpoint_url"] = 'https://88c8d6eb1b7f795dd10db7450be651ef.r2.cloudflarestorage.com'
else:
    MEDIA_URL = _media["MEDIA_URL"]

MEDIA_ROOT = _media["MEDIA_ROOT"]
USE_CLOUD_MEDIA = _media["USE_CLOUD_MEDIA"]

# Injection finale dans Django
STORAGES = {
    "default": _media["STORAGES_DEFAULT"],
    "staticfiles": {"BACKEND": _staticfiles_backend},
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024  
FILE_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024

# --- SÉCURITÉ HTTPS EN PRODUCTION ---
if not DEBUG:
    # On indique à Django de faire confiance aux en-têtes SSL de Render
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # CORRECTION : On passe temporairement à False pour stopper la boucle infinie de redirection 301.
    # Note : Render force déjà le HTTPS au niveau de ses routeurs par défaut.
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- AUTHENTICATION CONFIGURATION (ALLAUTH) ---
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/compte/connexion/"

AUTHENTICATION_BACKENDS = [
    "accounts.auth_backends.EmailPhoneUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"  

# --- EMAILS CONFIGURATION (GMAIL SMTP) ---
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "kadersoro18@gmail.com"
EMAIL_HOST_PASSWORD = "zkdjhevmnwkemqed"
DEFAULT_FROM_EMAIL = f"Kolê Group <{EMAIL_HOST_USER}>"

EMAIL_VERIFICATION_MAX_AGE = 48 * 3600

# --- GENIUSPAY ---
GENIUS_API_KEY = config("GENIUS_API_KEY", default="").strip()
GENIUS_API_SECRET = config("GENIUS_API_SECRET", default="").strip()
GENIUS_WEBHOOK_SECRET = config("GENIUS_WEBHOOK_SECRET", default="").strip()
GENIUS_DEFAULT_COUNTRY = config("GENIUS_DEFAULT_COUNTRY", default="CI").strip() or "CI"

# --- LOGS ---
if not DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {"class": "logging.StreamHandler", "stream": sys.stdout},
        },
        "root": {"handlers": ["console"], "level": "INFO"},
        "loggers": {
            "django.request": {
                "handlers": ["console"],
                "level": "ERROR",
                "propagate": False,
            },
        },
    }

# gestion_quitus_PAL/settings.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Charger les variables d'environnement depuis le fichier .env
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'quitus_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Middlewares de sécurité personnalisés
    'quitus_app.middleware.RateLimitMiddleware',
    'quitus_app.middleware.SecurityHeadersMiddleware',
    'quitus_app.middleware.SuspiciousActivityMiddleware',
]

ROOT_URLCONF = 'gestion_quitus_PAL.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_quitus_PAL.wsgi.application'

# Base MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'quitus_pal',
        'USER': 'root',
        'PASSWORD': 'root',  # Change avec ton mot de passe
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = False  # Désactiver le support des fuseaux horaires pour éviter les problèmes MySQL

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'quitus_app' / 'static',
]
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuration de la cache pour le rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'quitus-cache',
    }
}

# Configuration du logging pour l'audit
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'audit.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'quitus_audit': {
            'handlers': ['audit_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'quitus_security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# Créer le dossier logs s'il n'existe pas
import os
logs_dir = BASE_DIR / 'logs'
os.makedirs(logs_dir, exist_ok=True)

# ============================================================================
# Configuration Email - Phase 7: Notifications
# ============================================================================

# Backend email (console pour développement, SMTP pour production)
# Utiliser FORCE_EMAIL_SMTP=True dans .env pour forcer SMTP même en DEBUG
FORCE_EMAIL_SMTP = os.getenv('FORCE_EMAIL_SMTP', 'False') == 'True'

if DEBUG and not FORCE_EMAIL_SMTP:
    # En développement: affiche les emails dans la console
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # En production ou si FORCE_EMAIL_SMTP: utilise SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Configuration SMTP (à personnaliser selon votre serveur)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')  # Serveur SMTP
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))          # Port SMTP (587 pour TLS, 465 pour SSL)
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'  # Utiliser TLS (port 587)
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'  # Utiliser SSL (port 465)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')      # Votre email
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')  # Mot de passe
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@togoport.tg')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', 'noreply@togoport.tg')

# Configuration pour les notifications
NOTIFICATION_DAYS_BEFORE_EXPIRY = 7  # Envoyer email 7 jours avant expiration
NOTIFICATION_MAX_RETRIES = 3  # Nombre de tentatives si erreur
NOTIFICATION_RETRY_DELAY = 3600  # Délai avant nouvelle tentative (en secondes)

# Utiliser le backend en mémoire lors de l'exécution des tests pour capturer les emails dans django.core.mail.outbox
if 'test' in sys.argv:
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    # Bascule la base sur SQLite en mémoire pour accélérer et éviter dépendances MySQL pendant les tests
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'test_db.sqlite3',  # fichier persistant (plutôt que :memory: pour migrations)
        }
    }
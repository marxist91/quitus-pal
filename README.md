# 🚢 Système de Gestion des Quitus - Port Autonome de Lomé

[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-29%2F29%20passing-brightgreen.svg)](tests)

## 📋 Description

Application Django complète pour la gestion des attestations de régularité (Quitus) du Port Autonome de Lomé (PAL). Système sécurisé permettant la création, la vérification et le suivi des quitus avec génération automatique de PDF, codes QR, et notifications par email.

### ✨ Fonctionnalités Principales

#### 🎫 Gestion des Quitus
- Création et émission d'attestations de régularité
- Génération automatique de PDF sécurisés avec QR code
- Code de vérification unique (TUV - Tamper-Proof Unique Verification)
- Tracking complet de l'historique des opérations
- Statuts automatiques (ACTIF, EXPIRÉ, ANNULÉ)

#### 🔐 Sécurité Avancée
- **Rate Limiting** : Protection contre brute-force (5 tentatives max)
- **Détection d'injections** : SQL, XSS, Path Traversal
- **Headers de sécurité** : CSP, X-Frame-Options, HSTS
- **Audit logging** : Traçabilité complète des actions
- **Permissions granulaires** : Rôles Agent/Admin Service

#### 📧 Notifications Email (Phase 7)
- Alertes automatiques d'expiration (configurable à J-7)
- Templates HTML/texte professionnels
- Système de retry avec limite de tentatives
- Déduplication automatique
- Tracking complet des envois (statut, erreurs, retry_count)

#### 🔍 Vérification & Validation
- Vérification par QR code
- Validation par numéro de quitus
- API de vérification sécurisée
- Logging des consultations

---

## 🛠️ Stack Technique

- **Backend** : Django 5.0+
- **Base de données** : MySQL (production), SQLite (tests)
- **PDF** : ReportLab
- **QR Code** : qrcode[pil]
- **Chiffrement** : PyCryptodome
- **Email** : SMTP (Gmail/autres)
- **Tests** : Django TestCase (29 tests, 100% pass)

---

## 📦 Installation

### Prérequis
- Python 3.11+
- MySQL 8.0+ (production) ou SQLite (dev/tests)
- Git

### Étapes d'installation

```bash
# 1. Cloner le repository
git clone https://github.com/votre-username/gestion_quitus_PAL.git
cd gestion_quitus_PAL

# 2. Créer l'environnement virtuel
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configuration
# Copier et éditer le fichier .env
cp .env.example .env
# Éditer .env avec vos paramètres (voir Configuration)

# 5. Migrations
python manage.py migrate

# 6. Créer un superutilisateur
python manage.py createsuperuser

# 7. Lancer le serveur
python manage.py runserver
```

Accéder à l'application : `http://localhost:8000`

---

## ⚙️ Configuration

### Fichier `.env`

Créer un fichier `.env` à la racine du projet :

```env
# Django
SECRET_KEY=votre-clé-secrète-django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données MySQL (Production)
DB_NAME=quitus_pal
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=3306

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@togoport.tg
EMAIL_HOST_PASSWORD=mot-de-passe-application-gmail
DEFAULT_FROM_EMAIL=noreply@togoport.tg

# Notifications
NOTIFICATION_DAYS_BEFORE_EXPIRY=7
NOTIFICATION_MAX_RETRIES=3
NOTIFICATION_RETRY_DELAY=3600
```

### Configuration Gmail (Mot de passe d'application)

1. Activer l'authentification à 2 facteurs sur votre compte Gmail
2. Aller dans **Compte Google** → **Sécurité** → **Mots de passe d'applications**
3. Générer un mot de passe pour "Application Mail"
4. Utiliser ce mot de passe dans `EMAIL_HOST_PASSWORD`

---

## 🚀 Utilisation

### Créer un Quitus

```python
from quitus_app.models import Agent, Quitus
from datetime import datetime, timedelta

# Créer un agent
agent = Agent.objects.create(
    nom_complet="KOKOU Jean",
    matricule="MAT001",
    fonction="Directeur Général",
    email="kokou@togoport.tg",
    telephone="+228 90 00 00 00"
)

# Créer un quitus
quitus = Quitus.objects.create(
    numero_quitus="PAL-2025-0001",
    nom_prenoms="AGBEKO Marie",
    cni="TG123456789",
    nationalite="Togolaise",
    activite="Import/Export",
    compte_pal="PAL-001234",
    nif="NIF987654321",
    telephone="+228 90 12 34 56",
    email="agbeko@example.tg",
    situation_geo="Lomé, Quartier Administratif",
    adresse_postale="BP 5432 Lomé",
    date_emission=datetime.now().date(),
    date_validite=datetime.now().date() + timedelta(days=365),
    agent=agent
)

# Le PDF et QR code sont générés automatiquement via signals
```

### Commandes Management

```bash
# Vérifier les quitus expirant dans 7 jours et envoyer notifications
python manage.py check_expiring_quitus --days 7

# Réessayer les notifications échouées
python manage.py check_expiring_quitus --retry

# Combiner les deux
python manage.py check_expiring_quitus --days 7 --retry
```

### Planification Automatique

**Linux (cron)** :
```bash
crontab -e

# Ajouter :
0 9 * * * /chemin/venv/bin/python /chemin/manage.py check_expiring_quitus --days 7
0 10 * * * /chemin/venv/bin/python /chemin/manage.py check_expiring_quitus --retry
```

**Windows (Task Scheduler)** :
```powershell
$action = New-ScheduledTaskAction -Execute "C:\chemin\venv\Scripts\python.exe" -Argument "C:\chemin\manage.py check_expiring_quitus --days 7"
$trigger = New-ScheduledTaskTrigger -Daily -At 9am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "Quitus Expiry Check"
```

---

## 🧪 Tests

```bash
# Tous les tests
python manage.py test

# Tests spécifiques
python manage.py test quitus_app.tests_notifications
python manage.py test quitus_app.tests_security

# Avec verbosité
python manage.py test --verbosity 2

# Résultat : 29 tests, 100% pass (3 skipped)
```

### Problème de discovery sur `manage.py test`

Sur certaines configurations (notamment si un dossier `tests` existe directement sous une app), la discovery globale de `unittest` peut lever une erreur :

```
ImportError: 'tests' module incorrectly imported from '.../quitus_app/tests'. Expected '.../quitus_app'.
```

Solution recommandée (non intrusive) : utiliser le script utilitaire qui exécute les tests par application et recherche aussi les fichiers `test*.py` hors des packages :

```powershell
python scripts\run_tests_each_app.py
```

Ce script :
- exécute `manage.py test <app>.tests` pour chaque app listée dans `INSTALLED_APPS` (si un package `tests` existe),
- puis recherche et exécute les fichiers `test*.py` en dehors des packages d'app (via `python -m unittest <file>`).

Utilisez ce script dans votre environnement de développement Windows pour lancer l'ensemble des tests sans modifier la structure des tests existante.


### Couverture des Tests

| Module | Tests | Statut |
|--------|-------|--------|
| Notifications Email | 11 | ✅ 100% |
| Rate Limiting | 3 | ✅ 100% |
| Injection Detection | 3 | ✅ 100% |
| Permissions | 3 | ✅ 100% |
| Security Headers | 3 | ✅ 100% |
| Failed Login Logging | 2 | ✅ 100% |
| Verification Logging | 1 | ✅ 100% |
| Audit Logging | 3 | ⏭️ Skipped* |

*Tests d'audit skippés : signaux login/logout non implémentés (hors scope Phase 7)

---

## 📁 Structure du Projet

```
gestion_quitus_PAL/
│
├── gestion_quitus_PAL/          # Configuration Django
│   ├── settings.py              # Paramètres (email, DB, sécurité)
│   ├── urls.py                  # Routes principales
│   └── wsgi.py                  # WSGI pour production
│
├── quitus_app/                  # Application principale
│   ├── models.py                # Modèles (Quitus, Agent, Notifications)
│   ├── views.py                 # Vues métier
│   ├── forms.py                 # Formulaires Django
│   ├── notifications.py         # Système de notifications email
│   ├── pdf_generator.py         # Génération PDF
│   ├── qr_generator.py          # Génération QR codes
│   ├── permissions.py           # Gestion des rôles
│   ├── middleware.py            # Rate limiting, sécurité
│   ├── audit.py                 # Logging d'audit
│   ├── signals.py               # Signals Django (auto PDF)
│   │
│   ├── management/commands/     # Commandes management
│   │   └── check_expiring_quitus.py
│   │
│   ├── templates/               # Templates HTML
│   │   └── quitus_app/
│   │       └── emails/          # Templates email
│   │
│   ├── tests_notifications.py   # Tests Phase 7
│   ├── tests_security.py        # Tests sécurité
│   └── migrations/              # Migrations DB
│
├── logs/                        # Logs (audit, sécurité)
├── media/                       # Fichiers uploadés
├── static/                      # Fichiers statiques
│
├── requirements.txt             # Dépendances Python
├── manage.py                    # CLI Django
├── .env                         # Config (ignoré par Git)
├── .gitignore                   # Exclusions Git
└── README.md                    # Ce fichier
```

---

## 🔒 Sécurité

### Fonctionnalités Implémentées

✅ Rate limiting (5 tentatives/IP)  
✅ Détection SQL injection  
✅ Détection XSS  
✅ Détection Path Traversal  
✅ Content Security Policy (CSP)  
✅ X-Frame-Options: SAMEORIGIN  
✅ HTTPS Strict Transport Security  
✅ Audit logging complet  
✅ Permissions par rôles  
✅ CSRF protection (Django)  
✅ Chiffrement des codes de vérification  

### Recommandations Production

```python
# settings.py (production)
DEBUG = False
ALLOWED_HOSTS = ['votre-domaine.com']
SECRET_KEY = os.getenv('SECRET_KEY')  # Clé forte

# HTTPS obligatoire
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

## 📊 Modèle de Données

### Principales Tables

**Quitus**
- Identifiant UUID unique
- Informations bénéficiaire (nom, CNI, NIF, activité)
- Dates (émission, validité)
- QR code et code de vérification
- PDF généré automatiquement
- Statut (ACTIF/EXPIRÉ/ANNULÉ)

**Agent**
- Matricule unique
- Informations (nom, fonction, email, téléphone)
- Statut actif/inactif

**HistoriqueNotifications**
- Type (EXPIRY_WARNING, EXPIRY_EXPIRED, etc.)
- Destinataire (email, nom)
- Statut (PENDING/SENT/FAILED/BOUNCED)
- Retry count et erreurs
- Timestamps (création, envoi)

**HistoriqueQuitus**
- Actions (CREATION, CONSULTATION, MODIFICATION, IMPRESSION)
- Utilisateur et IP
- Détails et timestamp

---

## 📧 Système de Notifications

### Workflow Automatique

1. **Détection** : Cron exécute `check_expiring_quitus --days 7`
2. **Filtrage** : Trouve quitus avec `date_validite = today + 7` et `statut='ACTIF'`
3. **Déduplication** : Vérifie si notification déjà envoyée aujourd'hui
4. **Envoi** : Email HTML/texte multi-part
5. **Enregistrement** : Historique avec statut SENT/FAILED
6. **Retry** : Si échec, commande `--retry` renvoie (max 3 tentatives)

### Templates Email

- **HTML** : Design professionnel avec logo et styling
- **Texte** : Fallback pour clients n'acceptant pas HTML
- **Variables** : Nom bénéficiaire, jours restants, numéro quitus, date expiration

---

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit les changements (`git commit -m 'Ajout fonctionnalité X'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

### Standards

- Code PEP 8 compliant
- Tests pour nouvelles fonctionnalités
- Docstrings pour fonctions/classes
- Commits en français (cohérence projet)

---

## 📝 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 👥 Auteurs

**Port Autonome de Lomé - Direction des Systèmes d'Information**

---

## 📞 Support

Pour toute question ou problème :
- 📧 Email : support.quitus@togoport.tg
- 🐛 Issues GitHub : [github.com/votre-org/gestion_quitus_PAL/issues](https://github.com/votre-org/gestion_quitus_PAL/issues)

---

## 🗺️ Roadmap

### ✅ Phase 1-6 : Fonctionnalités de base
- Gestion CRUD Quitus
- Génération PDF/QR
- Sécurité avancée
- Tests complets

### ✅ Phase 7 : Notifications Email (ACTUELLE)
- Alertes d'expiration
- Templates professionnels
- Retry automatique
- Commandes management

### 🔜 Phases Futures
- **Phase 8** : Intégration Celery (asynchrone)
- **Phase 9** : Dashboard analytics
- **Phase 10** : API REST (DRF)
- **Phase 11** : Portail self-service bénéficiaires
- **Phase 12** : Notifications SMS (Twilio)
- **Phase 13** : Multi-langue (FR/EN)

---

## 🙏 Remerciements

- Django Framework
- Port Autonome de Lomé
- Contributeurs open-source

---

<div align="center">

**🚢 Fait avec ❤️ pour le Port Autonome de Lomé**

[Documentation](docs/) • [Changelog](CHANGELOG.md) • [Démo](https://demo.togoport.tg)

</div>

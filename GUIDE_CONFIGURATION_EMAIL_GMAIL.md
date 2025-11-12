# Guide de Configuration des Emails avec Gmail

## Problème
Les emails ne sont pas envoyés car Gmail nécessite un **mot de passe d'application** spécifique pour permettre aux applications tierces d'envoyer des emails.

## Solution : Créer un Mot de Passe d'Application Gmail

### Étape 1 : Activer la validation en deux étapes
1. Allez sur https://myaccount.google.com/security
2. Sous "Connexion à Google", cliquez sur **Validation en deux étapes**
3. Suivez les instructions pour l'activer si ce n'est pas déjà fait

### Étape 2 : Créer un mot de passe d'application
1. Allez sur https://myaccount.google.com/apppasswords
2. Connectez-vous avec votre compte Gmail (a.agbotse@togoport.tg)
3. Dans "Sélectionner l'application", choisissez **Autre (nom personnalisé)**
4. Tapez : `Django Quitus PAL`
5. Cliquez sur **Générer**
6. Gmail va générer un mot de passe de 16 caractères (ex: `abcd efgh ijkl mnop`)
7. **COPIEZ ce mot de passe** (vous ne le verrez qu'une fois)

### Étape 3 : Mettre à jour le fichier .env
Ouvrez le fichier `.env` et remplacez :
```
EMAIL_HOST_PASSWORD=mot-de-passe-application-gmail
```

Par :
```
EMAIL_HOST_PASSWORD=abcdefghijklmnop
```
(Utilisez le mot de passe généré, SANS espaces)

### Étape 4 : Redémarrer le serveur Django
```bash
# Arrêtez le serveur (Ctrl+C)
# Puis relancez :
python manage.py runserver
```

## Configuration Actuelle

Le fichier `.env` est configuré pour :
- **Serveur SMTP** : smtp.gmail.com
- **Port** : 587 (TLS)
- **Email expéditeur** : a.agbotse@togoport.tg
- **Nom affiché** : noreply@togoport.tg
- **FORCE_EMAIL_SMTP** : True (pour envoyer les emails même en mode DEBUG)

## Test de la Configuration

### Option 1 : Via la console Django
```bash
python manage.py shell
```

Puis dans le shell :
```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'Ceci est un email de test depuis Django.',
    'noreply@togoport.tg',
    ['votre-email-de-test@gmail.com'],
    fail_silently=False,
)
```

Si ça fonctionne, vous verrez : `1` (1 email envoyé)

### Option 2 : Via l'interface de suivi d'expirations
1. Allez sur la page **Suivi Expirations**
2. Cliquez sur "Envoyer notification" pour un quitus expirant bientôt
3. Vérifiez la boîte mail du destinataire

## Dépannage

### Erreur : "Authentication failed"
→ Le mot de passe d'application est incorrect. Regénérez-en un nouveau.

### Erreur : "SMTP AUTH extension not supported by server"
→ Vérifiez que `EMAIL_USE_TLS=True` dans `.env`

### Erreur : "Connection refused"
→ Vérifiez votre connexion internet et que le port 587 n'est pas bloqué par un firewall

### Les emails vont dans les spams
→ C'est normal avec Gmail. En production, utilisez un serveur SMTP professionnel (SendGrid, Mailgun, etc.)

## Alternative : Serveur SMTP Professionnel

Pour un environnement de production, utilisez un service professionnel :

### SendGrid (Recommandé)
```env
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=votre-clé-api-sendgrid
DEFAULT_FROM_EMAIL=noreply@togoport.tg
```

### Mailgun
```env
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@votre-domaine.mailgun.org
EMAIL_HOST_PASSWORD=votre-clé-api-mailgun
DEFAULT_FROM_EMAIL=noreply@togoport.tg
```

## Logs

Les logs d'envoi d'emails se trouvent dans :
- Console du serveur Django
- Table `HistoriqueNotifications` dans la base de données
- Fichier `logs/quitus_audit.log` (si configuré)

Pour voir les notifications dans la base :
```sql
SELECT * FROM quitus_app_historiquenotifications 
ORDER BY created_at DESC 
LIMIT 10;
```

## Résumé

1. ✅ Activer la validation en deux étapes sur Gmail
2. ✅ Créer un mot de passe d'application
3. ✅ Copier le mot de passe dans `.env` (EMAIL_HOST_PASSWORD)
4. ✅ Vérifier que FORCE_EMAIL_SMTP=True
5. ✅ Redémarrer le serveur Django
6. ✅ Tester l'envoi d'email

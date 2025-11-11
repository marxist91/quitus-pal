# 🔄 Guide de Réinitialisation de la Base de Données

## Étapes à Suivre

### 1. Supprimer les fichiers de migration existants

Ouvrez PowerShell dans le dossier du projet et exécutez :

```powershell
# Supprimer les fichiers de migration
Remove-Item .\quitus_app\migrations\0*.py -Force

# Vérifier que seul __init__.py reste
Get-ChildItem .\quitus_app\migrations\
```

### 2. Réinitialiser la base de données MySQL

```powershell
# Ouvrir MySQL en ligne de commande
mysql -u root -proot
```

Puis dans MySQL :

```sql
-- Supprimer l'ancienne base
DROP DATABASE IF EXISTS quitus_pal;

-- Créer la nouvelle base
CREATE DATABASE quitus_pal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Vérifier
SHOW DATABASES;

-- Quitter
EXIT;
```

### 3. Créer les nouvelles migrations

```powershell
python manage.py makemigrations
```

Vous devriez voir :
```
Migrations for 'quitus_app':
  quitus_app\migrations\0001_initial.py
    - Create model Agent
    - Create model Quitus
    - Create model HistoriqueQuitus
    - ...
```

### 4. Appliquer les migrations

```powershell
python manage.py migrate
```

Vous devriez voir :
```
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
  Applying quitus_app.0001_initial... OK
```

### 5. Créer le superutilisateur

```powershell
python manage.py createsuperuser
```

**Informations à saisir :**
- Username: `marcel`
- Email: `marcel@togoport.tg`
- Password: `TogoPort2024@` (ou votre choix)
- Confirmer le password

### 6. Mettre à jour le prénom et nom (optionnel)

```powershell
python manage.py shell
```

Dans le shell Python :

```python
from django.contrib.auth.models import User
user = User.objects.get(username='marcel')
user.first_name = 'Marcel'
user.last_name = 'KOKOU'
user.save()
exit()
```

### 7. Démarrer le serveur

```powershell
python manage.py runserver
```

### 8. Se connecter

Ouvrez votre navigateur : `http://localhost:8000/login/`

**Identifiants :**
- Email/Username: `marcel@togoport.tg` ou `marcel`
- Mot de passe: `TogoPort2024@`

## ✅ Vérifications

Une fois connecté, vérifiez que :

1. **Navbar affiche** : "Marcel KOKOU" (et non "marcel")
2. **Menu dropdown contient** :
   - ✅ Changer le mot de passe
   - ✅ Administration Django (si superuser)
   - ✅ Déconnexion

3. **Page d'accueil affiche** :
   - ✅ Créer un Quitus
   - ✅ Liste des Quitus
   - ✅ Recherche
   - ✅ Gestion Utilisateurs (si admin/staff)

4. **Dashboard Utilisateurs** :
   - Accédez à "Gestion Utilisateurs"
   - Créez un utilisateur de test
   - Laissez le mot de passe vide → vérifie que `TogoPort2024@` fonctionne

5. **Changement de mot de passe** :
   - Cliquez sur votre nom → "Changer le mot de passe"
   - Changez le mot de passe
   - Vérifiez que vous restez connecté

6. **Connexion par email** :
   - Déconnectez-vous
   - Reconnectez-vous avec `marcel@togoport.tg`
   - Vérifiez que ça fonctionne

## 🎯 Résultat Attendu

Après la réinitialisation, vous aurez :

- ✅ Base de données MySQL propre avec nouvelles tables
- ✅ Superutilisateur "Marcel KOKOU" créé
- ✅ Authentification par email fonctionnelle
- ✅ Mot de passe par défaut pour nouveaux utilisateurs
- ✅ Interface de changement de mot de passe
- ✅ Nom complet affiché dans la navbar

## 🆘 En Cas de Problème

### Erreur : "No changes detected"
```powershell
# Forcer la création des migrations
python manage.py makemigrations quitus_app
```

### Erreur : "Table already exists"
```powershell
# Supprimer complètement la base et recommencer à l'étape 2
```

### Erreur MySQL : "Access denied"
```powershell
# Vérifier le mot de passe root dans settings.py
# Ligne: 'PASSWORD': 'root',
```

### Serveur ne démarre pas
```powershell
# Vérifier les erreurs
python manage.py check

# Vérifier les migrations
python manage.py showmigrations
```

## 📝 Commandes Utiles

```powershell
# Voir toutes les migrations
python manage.py showmigrations

# Voir le SQL d'une migration
python manage.py sqlmigrate quitus_app 0001

# Vérifier la configuration
python manage.py check

# Créer des données de test
python manage.py shell
```

---

**Date** : 10 novembre 2025  
**Statut** : Prêt pour réinitialisation  
**Version** : 1.0 avec gestion des mots de passe

# 📋 Commandes de Réinitialisation - À Exécuter Manuellement

## ✅ ÉTAPE 1 : Migrations supprimées (DÉJÀ FAIT)

Les anciens fichiers de migration ont déjà été supprimés.

## 🔄 ÉTAPE 2 : Réinitialiser MySQL

Ouvrez un terminal MySQL :

```bash
mysql -u root -proot
```

Dans MySQL, exécutez :

```sql
DROP DATABASE IF EXISTS quitus_pal;
CREATE DATABASE quitus_pal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
EXIT;
```

## 🔧 ÉTAPE 3 : Créer les migrations

```bash
python manage.py makemigrations
```

**Résultat attendu :**
```
Migrations for 'quitus_app':
  quitus_app\migrations\0001_initial.py
    - Create model Agent
    - Create model Quitus
    - Create model HistoriqueQuitus
    - Create model HistoriqueNotifications
```

## 📊 ÉTAPE 4 : Appliquer les migrations

```bash
python manage.py migrate
```

**Résultat attendu :**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, quitus_app, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
  Applying quitus_app.0001_initial... OK
```

## 👤 ÉTAPE 5 : Créer le superutilisateur

### Option A : Avec invite interactive
```bash
python manage.py createsuperuser
```

Saisissez :
- **Username:** marcel
- **Email:** marcel@togoport.tg
- **Password:** TogoPort2024@
- **Password (again):** TogoPort2024@

### Option B : Sans interaction (automatique)
```bash
set DJANGO_SUPERUSER_PASSWORD=TogoPort2024@
python manage.py createsuperuser --noinput --username marcel --email marcel@togoport.tg
```

## 🎨 ÉTAPE 6 : Configurer le prénom et nom

```bash
python manage.py shell
```

Dans le shell Python :
```python
from django.contrib.auth.models import User
user = User.objects.get(username='marcel')
user.first_name = 'Marcel'
user.last_name = 'KOKOU'
user.save()
print(f"✓ Utilisateur: {user.get_full_name()}")
exit()
```

## 🚀 ÉTAPE 7 : Démarrer le serveur

```bash
python manage.py runserver
```

## 🔐 ÉTAPE 8 : Tester la connexion

1. Ouvrez : http://localhost:8000/login/
2. **Connexion avec email :**
   - Email: `marcel@togoport.tg`
   - Mot de passe: `TogoPort2024@`

3. **OU connexion avec username :**
   - Username: `marcel`
   - Mot de passe: `TogoPort2024@`

## ✅ Vérifications Post-Installation

### 1. Navbar affiche le nom complet
✅ Devrait afficher : "Marcel KOKOU" (et non "marcel")

### 2. Menu dropdown
✅ Doit contenir :
- Changer le mot de passe
- Administration Django
- Déconnexion

### 3. Tester le changement de mot de passe
1. Cliquez sur "Marcel KOKOU" → "Changer le mot de passe"
2. Ancien mot de passe: `TogoPort2024@`
3. Nouveau mot de passe: (votre choix, min 8 caractères)
4. Confirmer le nouveau mot de passe
5. ✅ Vous devez rester connecté après le changement

### 4. Tester la création d'utilisateur
1. Allez sur "Gestion Utilisateurs"
2. Cliquez "Ajouter un utilisateur"
3. Remplissez :
   - Username: `test`
   - Email: `test@togoport.tg`
   - Prénom: `Test`
   - Nom: `USER`
   - Rôle: Agent
   - **Laissez les mots de passe vides**
4. Sauvegardez
5. ✅ L'utilisateur doit être créé avec le mot de passe par défaut `TogoPort2024@`

### 5. Tester la connexion par email du nouvel utilisateur
1. Déconnectez-vous
2. Connectez-vous avec:
   - Email: `test@togoport.tg`
   - Mot de passe: `TogoPort2024@`
3. ✅ La connexion doit réussir
4. ✅ La navbar doit afficher "Test USER"

## 🎯 Résumé

Une fois toutes ces étapes complétées, vous aurez :

✅ Base de données MySQL propre
✅ Toutes les tables créées
✅ Superutilisateur "Marcel KOKOU" configuré
✅ Authentification par email fonctionnelle
✅ Mot de passe par défaut pour nouveaux utilisateurs
✅ Interface de changement de mot de passe opérationnelle
✅ Nom complet affiché dans la navbar

## 🆘 Aide Rapide

**Si une commande échoue :**
```bash
# Vérifier l'état
python manage.py check

# Voir les migrations
python manage.py showmigrations

# Voir les erreurs détaillées
python manage.py migrate --verbosity 3
```

**Si vous devez tout recommencer :**
1. Supprimez `quitus_app\migrations\0*.py`
2. Recommencez à l'étape 2 (DROP DATABASE)

---

**Note :** Exécutez ces commandes dans l'ordre. Chaque étape doit réussir avant de passer à la suivante.

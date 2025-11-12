# Configuration des Groupes et Permissions - Système Quitus PAL

## 📋 TROIS RÔLES DÉFINIS

### 1. 🔵 AGENT (Simple Utilisateur)
**Rôle**: Agent de service qui crée et gère ses propres quitus

**Permissions**:
- ✅ Créer des quitus (`add_quitus`)
- ✅ Voir ses propres quitus uniquement (`view_quitus`)
- ✅ Envoyer des notifications (`add_historiquenotifications`, `view_historiquenotifications`)
- ✅ Consulter l'historique de ses quitus (`view_historiquequitus`)
- ✅ Voir les profils utilisateurs (`view_userprofile`)

**Restrictions**:
- ❌ Ne peut PAS modifier ou supprimer des quitus
- ❌ Ne peut PAS voir les quitus des autres agents
- ❌ Pas d'accès aux statistiques globales
- ❌ Ne peut PAS créer d'utilisateurs

---

### 2. 🟢 CHEF_DIRECTEUR
**Rôle**: Chef de service / Directeur avec pouvoir de gestion et supervision

**Permissions**:
- ✅ **Toutes les permissions Agent** +
- ✅ Modifier tous les quitus (`change_quitus`)
- ✅ Supprimer tous les quitus (`delete_quitus`)
- ✅ Voir TOUS les quitus (pas seulement les siens)
- ✅ Accès aux statistiques et dashboard
- ✅ Créer des utilisateurs (`add_user`)
- ✅ Modifier des utilisateurs (`change_user`)
- ✅ Gérer les UserProfile (`add_userprofile`, `change_userprofile`)
- ✅ Voir tous les historiques
- ✅ Gérer toutes les notifications

**Restrictions**:
- ❌ Ne peut PAS supprimer des utilisateurs
- ❌ Ne peut PAS modifier les groupes et permissions système

---

### 3. 🔴 SUPERUSER (Admin Plateforme)
**Rôle**: Administrateur système avec accès total

**Permissions**:
- ✅ **ACCÈS TOTAL** à toutes les fonctionnalités
- ✅ Gestion complète Django Admin
- ✅ Créer, modifier, **supprimer** des utilisateurs
- ✅ Modifier les groupes et permissions
- ✅ Accès à tous les modèles et données
- ✅ Configuration système

**Note**: Le superuser n'a pas besoin de groupe, son statut `is_superuser=True` lui donne tous les droits.

---

## 🚀 MISE EN PLACE

### Étape 1: Exécuter la commande de configuration
```bash
python manage.py setup_permissions
```

Cette commande:
1. Crée automatiquement les groupes `Agent` et `Chef_Directeur`
2. Assigne les permissions appropriées à chaque groupe
3. Affiche un résumé des utilisateurs existants

### Étape 2: Assigner les utilisateurs aux groupes

#### Via Django Admin:
1. Connectez-vous à `/admin/`
2. Allez dans **Authentification et autorisation → Utilisateurs**
3. Sélectionnez un utilisateur
4. Dans la section **Permissions**:
   - Pour un **Agent**: Cochez le groupe `Agent`
   - Pour un **Chef_Directeur**: Cochez le groupe `Chef_Directeur`
   - Pour un **Superuser**: Cochez `Statut de super-utilisateur`
5. Sauvegardez

#### Via shell Python:
```python
python manage.py shell

from django.contrib.auth.models import User, Group

# Assigner un utilisateur au groupe Agent
user = User.objects.get(username='nom_utilisateur')
agent_group = Group.objects.get(name='Agent')
user.groups.add(agent_group)

# Assigner un utilisateur au groupe Chef_Directeur
user = User.objects.get(username='nom_utilisateur')
chef_group = Group.objects.get(name='Chef_Directeur')
user.groups.add(chef_group)

# Créer un superuser
user = User.objects.get(username='nom_utilisateur')
user.is_superuser = True
user.is_staff = True
user.save()
```

---

## 🔐 CONTRÔLE D'ACCÈS DANS LES VUES

Le système utilise des décorateurs pour contrôler l'accès:

```python
from quitus_app.permissions import role_required, admin_required, agent_required

# Vue accessible uniquement aux agents (et supérieurs)
@agent_required
def creer_quitus(request):
    ...

# Vue accessible uniquement aux chefs et superusers
@admin_required
def dashboard_stats(request):
    ...

# Vue accessible à plusieurs rôles
@role_required('admin_service', 'admin_plateforme')
def manage_users(request):
    ...
```

---

## 📊 VUES PROTÉGÉES ACTUELLES

### Accessibles aux AGENTS:
- `/creer/` - Créer un quitus
- `/liste/` - Voir ses quitus
- `/detail/<numero>/` - Détails d'un quitus
- `/telecharger/<numero>/` - Télécharger un quitus
- `/verifier/<code>/` - Vérifier un quitus
- `/expiry-monitor/` - Voir ses quitus qui expirent bientôt
- `/send-expiry-notification/<id>/` - Envoyer une notification

### Accessibles aux CHEF_DIRECTEUR (+ Agents):
- `/dashboard/stats/` - Statistiques par utilisateur
- `/dashboard/users/` - Gestion des utilisateurs
- `/recherche/` - Recherche avancée
- `/export/csv/` - Export CSV
- `/export/excel/` - Export Excel
- `/annuler/<numero>/` - Annuler un quitus
- `/edit/<numero>/` - Modifier un quitus
- `/manage-roles/` - Gérer les rôles
- `/notifications/` - Voir toutes les notifications
- `/send-bulk-notifications/` - Envoi groupé

### Accessibles aux SUPERUSERS uniquement:
- `/admin/` - Django Admin complet
- Suppression d'utilisateurs
- Modification des permissions système

---

## ✅ VÉRIFICATION

### Vérifier les groupes créés:
```bash
python manage.py shell
from django.contrib.auth.models import Group
print(Group.objects.all())
# Résultat attendu: <QuerySet [<Group: Agent>, <Group: Chef_Directeur>]>
```

### Vérifier les permissions d'un groupe:
```python
agent_group = Group.objects.get(name='Agent')
for perm in agent_group.permissions.all():
    print(f"{perm.codename} - {perm.name}")
```

### Vérifier le rôle d'un utilisateur:
```python
from django.contrib.auth.models import User
user = User.objects.get(username='nom_utilisateur')
print(f"Superuser: {user.is_superuser}")
print(f"Groupes: {[g.name for g in user.groups.all()]}")
```

---

## 🔄 MIGRATION DES UTILISATEURS EXISTANTS

Si vous avez des utilisateurs existants, assignez-les aux groupes appropriés:

```python
python manage.py shell

from django.contrib.auth.models import User, Group

agent_group = Group.objects.get(name='Agent')
chef_group = Group.objects.get(name='Chef_Directeur')

# Exemple: Assigner l'utilisateur "petit" au groupe Agent
petit = User.objects.get(username='petit')
petit.groups.add(agent_group)

# Exemple: Assigner l'utilisateur "paul" au groupe Chef_Directeur
paul = User.objects.get(username='paul')
paul.groups.add(chef_group)
paul.is_staff = True  # Accès Django Admin
paul.save()

# Exemple: L'utilisateur "marcel" reste superuser
marcel = User.objects.get(username='marcel')
# Déjà configuré avec is_superuser=True
```

---

## 📝 NOTES IMPORTANTES

1. **Hiérarchie des rôles**: Superuser > Chef_Directeur > Agent
   - Un superuser a TOUS les droits
   - Un Chef_Directeur a tous les droits d'un Agent + plus
   - Un Agent a les droits de base uniquement

2. **is_staff vs is_superuser**:
   - `is_staff=True` : Accès à Django Admin
   - `is_superuser=True` : Tous les droits (inclut is_staff)
   - Recommandé: `is_staff=True` pour Chef_Directeur

3. **Protection dans les vues**:
   - Les vues vérifient automatiquement les permissions
   - Les agents ne voient que LEURS quitus (filtre automatique)
   - Les chefs et superusers voient TOUS les quitus

4. **UserProfile**:
   - Créé automatiquement pour chaque nouvel utilisateur
   - Stocke: matricule, fonction, telephone, actif
   - Accessible via `user.userprofile`

---

## 🆘 DÉPANNAGE

### "Permission denied" même après assignation du groupe
- Déconnectez-vous et reconnectez-vous
- Vérifiez que l'utilisateur est actif (`is_active=True`)
- Vérifiez les permissions du groupe dans Django Admin

### Les vues ne filtrent pas correctement par rôle
- Vérifiez que les décorateurs sont appliqués aux vues
- Consultez `quitus_app/permissions.py` pour les fonctions de vérification
- Assurez-vous que `is_staff=True` pour les Chef_Directeur

### Impossible d'accéder à Django Admin
- Vérifiez `is_staff=True` ET (`is_superuser=True` OU groupe Chef_Directeur)
- L'URL est `/admin/`
- Seuls les superusers et staff peuvent accéder

---

Généré le: {{ date }}
Version: 1.0

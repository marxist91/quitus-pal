# 📅 Suivi des Expirations - Guide Complet

## ✅ Résumé

Une nouvelle page dédiée au **monitoring des dates d'expiration** a été créée avec succès ! Cette interface utilise un système de **codes couleur** (🟢 Vert, 🟡 Jaune, 🔴 Rouge) pour identifier rapidement les quitus selon leur urgence d'expiration.

## 🎯 Fonctionnalités

### 1. **Page de Suivi des Expirations**
- **URL :** `http://127.0.0.1:8000/expiry-monitor/`
- **Accès :** Navbar → "Suivi Expirations" OU Page d'accueil → Carte "Suivi Expirations"

#### Système de Codes Couleur
| Couleur | Critère | Signification | Badge |
|---------|---------|---------------|-------|
| 🟢 **Vert** | Plus de 7 jours | Sûr - Aucune action immédiate | success |
| 🟡 **Jaune** | 1 à 7 jours | Attention - Action recommandée | warning |
| 🔴 **Rouge** | Expire aujourd'hui ou expiré | Critique - Action urgente | danger |

#### Cartes Statistiques
Affichage en temps réel :
- **Sûr (Vert)** : Nombre de quitus avec plus de 7 jours restants
- **Attention (Jaune)** : Nombre de quitus expirant dans 1-7 jours
- **Critique (Rouge)** : Nombre de quitus expirés ou expirant aujourd'hui
- **Total** : Nombre total de quitus actifs

### 2. **Filtres Disponibles**

#### Pour les Agents
- **Statut d'Expiration** : Vert, Jaune, Rouge, ou Tous
- Affichage restreint : Uniquement leurs propres quitus

#### Pour les Chefs/Admins
- **Agent** : Filtrer par agent spécifique ou voir tous
- **Statut d'Expiration** : Vert, Jaune, Rouge, ou Tous

### 3. **Tableau Détaillé**

Colonnes affichées :
| Colonne | Description |
|---------|-------------|
| **Indicateur** | Pastille colorée animée (pulsation) |
| **Numéro Quitus** | Lien cliquable vers les détails |
| **Bénéficiaire** | Nom du bénéficiaire |
| **Agent** | Agent ayant créé le quitus |
| **Date Validité** | Date d'expiration (format JJ/MM/AAAA) |
| **Jours Restants** | Badge coloré avec nombre de jours |
| **Statut** | Description textuelle (ex: "Expire dans 3 jour(s)") |
| **Notification** | Envoyée ou Aucune |
| **Actions** | Boutons Notifier et Voir détails |

### 4. **Actions Disponibles**

#### Envoyer une Notification Individuelle
- Bouton "📧 Notifier" sur chaque ligne
- Envoie un email d'avertissement au bénéficiaire
- Désactivé si aucun email disponible
- Message de confirmation après envoi

#### Envoyer Toutes les Notifications (Chef/Admin uniquement)
- Bouton "Envoyer Toutes les Notifications" dans l'en-tête des filtres
- Envoie des notifications pour tous les quitus expirant dans les 7 jours
- Évite les doublons (ne renvoie pas si déjà envoyé aujourd'hui)
- Rapport détaillé : X succès, Y échecs

## 🎨 Design et Interface

### Codes Couleur des Lignes
- **Ligne verte claire** : Quitus sûr (> 7 jours)
- **Ligne jaune claire** : Quitus attention (1-7 jours)
- **Ligne rouge claire** : Quitus critique (expiré)

### Animations
- **Pastille de statut** : Animation de pulsation (2s)
- **Transition douce** : Hover sur les lignes

### Responsive Design
- Tableau scrollable horizontalement sur mobile
- En-têtes sticky (restent visibles au scroll)
- Cartes empilées sur petit écran

## 🔐 Permissions

| Fonctionnalité | Agent | Chef | Admin |
|----------------|-------|------|-------|
| Voir suivi expirations | ✅ (ses quitus) | ✅ (tous) | ✅ (tous) |
| Filtrer par agent | ❌ | ✅ | ✅ |
| Envoyer notification individuelle | ✅ (ses quitus) | ✅ | ✅ |
| Envoyer toutes les notifications | ❌ | ✅ | ✅ |

## 🚀 Utilisation

### Cas 1 : Agent Vérifiant ses Quitus
1. Se connecter avec compte agent
2. Aller sur "Suivi Expirations" (navbar ou page d'accueil)
3. Voir uniquement ses quitus triés par date de validité
4. Repérer les lignes jaunes/rouges
5. Cliquer sur "📧 Notifier" pour envoyer un email au bénéficiaire

### Cas 2 : Chef Surveillant l'Équipe
1. Se connecter avec compte chef
2. Aller sur "Suivi Expirations"
3. Voir tous les quitus de tous les agents
4. Filtrer par agent spécifique si besoin
5. Filtrer par statut rouge pour voir les critiques
6. Cliquer sur "Envoyer Toutes les Notifications" pour notifier tous les quitus jaunes/rouges

### Cas 3 : Admin Analysant les Tendances
1. Se connecter avec compte admin
2. Aller sur "Suivi Expirations"
3. Consulter les cartes statistiques :
   - Vert : X quitus sûrs
   - Jaune : Y quitus à surveiller
   - Rouge : Z quitus critiques
4. Filtrer par couleur pour analyser chaque catégorie
5. Envoyer notifications groupées si nécessaire

## 📧 Notifications Email

### Email d'Avertissement d'Expiration
**Sujet :** "Avertissement: Votre Quitus expirera dans X jours"

**Contenu :**
- Nom du bénéficiaire
- Numéro du quitus
- Date d'expiration
- Nombre de jours restants
- Message d'avertissement
- Instructions (renouvellement, contact, etc.)

### Déclencheurs
1. **Manuel** : Bouton "Notifier" sur la page
2. **Automatique** : Commande Django `check_expiring_quitus`
3. **Groupé** : Bouton "Envoyer Toutes les Notifications"

## 🤖 Envoi Automatique

### Commande Management Django

#### Utilisation de Base
```bash
python manage.py check_expiring_quitus
```
Vérifie les quitus expirant dans 7 jours (par défaut) et envoie des notifications.

#### Options Disponibles
```bash
# Vérifier pour une période différente
python manage.py check_expiring_quitus --days 3

# Retenter les notifications échouées
python manage.py check_expiring_quitus --retry

# Combiner les deux
python manage.py check_expiring_quitus --days 7 --retry
```

### Configuration d'une Tâche Planifiée (Cron)

#### Sur Linux/Mac
Ajouter dans crontab (`crontab -e`) :
```bash
# Exécuter tous les jours à 9h du matin
0 9 * * * cd /chemin/vers/projet && python manage.py check_expiring_quitus
```

#### Sur Windows (Task Scheduler)
1. Ouvrir "Planificateur de tâches"
2. Créer une tâche basique
3. Déclencheur : Quotidien à 9h00
4. Action : Démarrer un programme
   - Programme : `python`
   - Arguments : `manage.py check_expiring_quitus`
   - Répertoire : `C:\Users\marcel\gestion_quitus_PAL`

### Configuration Recommandée
```bash
# Tous les jours à 9h : Vérifier expirations dans 7 jours
0 9 * * * python manage.py check_expiring_quitus --days 7

# Tous les jours à 10h : Vérifier expirations dans 3 jours
0 10 * * * python manage.py check_expiring_quitus --days 3

# Tous les jours à 11h : Vérifier expirations dans 1 jour
0 11 * * * python manage.py check_expiring_quitus --days 1
```

## 📂 Fichiers Créés/Modifiés

### Nouveaux Fichiers
1. `quitus_app/templates/quitus_app/expiry_monitor.html` - Interface de suivi (300+ lignes)
2. `quitus_app/management/commands/check_expiring_quitus.py` - Commande automatique (existe déjà)

### Fichiers Modifiés
1. `quitus_app/views.py` :
   - `expiry_monitor()` - Vue principale avec catégorisation par couleur
   - `send_expiry_notification()` - Envoi manuel individuel
   - `send_all_expiry_notifications()` - Envoi groupé (chef/admin)

2. `quitus_app/urls.py` :
   - `path('expiry-monitor/', ...)` - Page de suivi
   - `path('expiry-monitor/<id>/send/', ...)` - Envoi individuel
   - `path('expiry-monitor/send-all/', ...)` - Envoi groupé

3. `quitus_app/templates/quitus_app/base.html` :
   - Ajout du lien "Suivi Expirations" dans la navbar

4. `quitus_app/templates/quitus_app/accueil.html` :
   - Ajout de la carte "Suivi Expirations"

## 🔍 Détails Techniques

### Logique de Catégorisation
```python
jours_restants = (date_validite - aujourd'hui).days

if jours_restants < 0:
    couleur = 'rouge'
    statut = f"Expiré depuis {abs(jours_restants)} jour(s)"
elif jours_restants == 0:
    couleur = 'rouge'
    statut = "Expire aujourd'hui"
elif jours_restants <= 7:
    couleur = 'jaune'
    statut = f"Expire dans {jours_restants} jour(s)"
else:
    couleur = 'vert'
    statut = f"Expire dans {jours_restants} jour(s)"
```

### Prévention des Doublons
- Vérification automatique : Notification déjà envoyée aujourd'hui ?
- Affichage du badge "Envoyée" si notification existante
- Skip automatique lors de l'envoi groupé

### Optimisations
- `select_related('agent')` : Évite N+1 queries
- Pagination : 50 quitus par page
- Indexes sur `date_validite` et `statut`
- Requête unique pour récupérer les quitus actifs

## 📊 Exemples de Scénarios

### Scénario 1 : Alerte Rouge
```
Quitus : Q-2025-001
Date validité : 11/01/2025 (dans 0 jours - aujourd'hui)
Couleur : 🔴 Rouge
Action : URGENCE - Envoyer notification immédiatement
```

### Scénario 2 : Attention Jaune
```
Quitus : Q-2025-002
Date validité : 15/01/2025 (dans 4 jours)
Couleur : 🟡 Jaune
Action : Envoyer notification pour rappel
```

### Scénario 3 : Sûr Vert
```
Quitus : Q-2025-003
Date validité : 30/01/2025 (dans 19 jours)
Couleur : 🟢 Vert
Action : Aucune action requise pour le moment
```

## 📈 Statistiques et Métriques

### Métriques Affichées
- Nombre total de quitus actifs
- Répartition par catégorie (vert/jaune/rouge)
- Pourcentage de quitus critiques
- Notifications envoyées vs en attente

### Exemple d'Affichage
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│   Sûr       │  Attention  │  Critique   │   Total     │
│   (Vert)    │   (Jaune)   │   (Rouge)   │             │
├─────────────┼─────────────┼─────────────┼─────────────┤
│     45      │     12      │      3      │     60      │
│    75%      │     20%     │     5%      │   100%      │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

## ⚡ Actions Rapides

### Envoyer une Notification
1. Trouver le quitus dans le tableau
2. Cliquer sur "📧 Notifier"
3. Confirmation automatique après envoi

### Filtrer les Critiques
1. Sélectionner "🔴 Rouge" dans le filtre Statut
2. Cliquer "Filtrer"
3. Ne voir que les quitus expirés ou expirant aujourd'hui

### Envoyer Toutes les Notifications
1. Cliquer sur "Envoyer Toutes les Notifications"
2. Confirmer l'action
3. Attendre le rapport de résultat

## 🐛 Résolution de Problèmes

### Problème : Bouton "Notifier" désactivé
**Cause :** Aucun email de bénéficiaire configuré  
**Solution :** Éditer le quitus pour ajouter un email

### Problème : Notification non envoyée
**Cause :** Configuration email incorrecte  
**Solution :** Vérifier `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT` dans settings.py

### Problème : Quitus ne s'affiche pas
**Cause :** Statut non "Actif" ou déjà expiré depuis longtemps  
**Solution :** Vérifier le statut du quitus dans la liste

### Problème : Statistiques incorrectes
**Cause :** Cache navigateur  
**Solution :** Rafraîchir la page (Ctrl+F5)

## 📚 Documentation Connexe

- **GUIDE_NOTIFICATIONS.md** - Système de notifications email
- **notifications.py** - Logique d'envoi des emails
- **models.py** - Modèle HistoriqueNotifications

## 🎯 Bonnes Pratiques

### Pour les Agents
1. Vérifier le suivi d'expiration **quotidiennement**
2. Envoyer des notifications dès qu'un quitus passe au jaune
3. Contacter les bénéficiaires pour les quitus rouges

### Pour les Chefs/Admins
1. Configurer l'envoi automatique quotidien (cron)
2. Surveiller les statistiques chaque matin
3. Suivre le taux de notifications envoyées vs échecs
4. Analyser les tendances d'expiration par agent

### Pour l'Équipe IT
1. Configurer les tâches planifiées (cron/Task Scheduler)
2. Monitorer les logs d'envoi d'email
3. Vérifier régulièrement la configuration SMTP
4. Maintenir une liste blanche des emails

## 💻 Commandes Utiles

### Vérification Manuelle
```bash
# Vérifier les quitus expirant dans 7 jours
python manage.py check_expiring_quitus --days 7

# Vérifier avec retry des échecs
python manage.py check_expiring_quitus --days 7 --retry
```

### Démarrer le Serveur
```bash
python manage.py runserver
```

### Tester l'Envoi d'Email
```bash
python manage.py sendtestemail votre@email.com
```

## 🌐 URLs Ajoutées

| URL | Description | Méthode | Accès |
|-----|-------------|---------|-------|
| `/expiry-monitor/` | Page de suivi des expirations | GET | Tous |
| `/expiry-monitor/<id>/send/` | Envoyer notification individuelle | POST | Tous (ses quitus) |
| `/expiry-monitor/send-all/` | Envoyer toutes les notifications | POST | Chef/Admin |

## 📊 Résumé de l'Implémentation

- ✅ **3 nouvelles vues** créées
- ✅ **3 nouvelles routes** ajoutées
- ✅ **1 template complet** avec codes couleur
- ✅ **Système de catégorisation** automatique (vert/jaune/rouge)
- ✅ **Filtres avancés** par agent et statut
- ✅ **Envoi manuel et groupé** de notifications
- ✅ **Commande automatique** déjà existante
- ✅ **Pagination** (50 par page)
- ✅ **Statistiques** en temps réel
- ✅ **Permissions** par rôle
- ✅ **Animations** et design moderne

## 🎉 C'est Prêt !

Le système de suivi des expirations est maintenant **100% fonctionnel** !

**Pour y accéder :**
1. Démarrer le serveur : `python manage.py runserver`
2. Se connecter : `http://127.0.0.1:8000/login/`
3. Navbar → "Suivi Expirations"
4. OU Page d'accueil → Carte "Suivi Expirations"

---

**Date de création :** Janvier 2025  
**Version :** 1.0  
**Développé pour :** Port Autonome de Lomé - Système de Gestion des Quitus

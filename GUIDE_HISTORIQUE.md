# 📋 Guide de l'Historique des Actions

## Vue d'ensemble

L'historique des actions est maintenant accessible de manière permanente via un lien dans la navbar, permettant à tous les utilisateurs de consulter leurs activités sans avoir besoin d'ouvrir un quitus spécifique.

## 🎯 Fonctionnalités

### Pour tous les utilisateurs authentifiés

- **Accès permanent** : Lien "Historique" visible dans la navbar pour tous les utilisateurs connectés
- **Vue personnalisée** : Chaque utilisateur voit ses propres actions
- **Filtres disponibles** :
  - Type d'action (LOGIN, LOGOUT, CREATE_QUITUS, etc.)
  - Numéro de quitus
  - Plage de dates (date de début et date de fin)
- **Pagination** : 25 entrées par page pour une navigation facile

### Pour les Admins et Chefs (is_staff ou is_superuser)

- **Vue globale** : Accès à TOUS les logs de TOUS les utilisateurs
- **Filtre utilisateur** : Possibilité de filtrer par nom d'utilisateur
- **Colonne utilisateur** : Affichage de qui a effectué chaque action

### Pour les Agents (utilisateurs standards)

- **Vue restreinte** : Uniquement leurs propres actions
- **Message informatif** : Alerte bleue indiquant "Vue restreinte : Vous voyez uniquement vos propres actions"
- **Interface simplifiée** : Pas de filtre utilisateur ni de colonne utilisateur (inutiles pour leur vue)

## 📍 Accès

1. **Via la navbar** : Cliquez sur "Historique" (icône horloge)
2. **URL directe** : `/history/`

## 🔍 Types d'actions enregistrées

- `LOGIN` : Connexion réussie
- `LOGOUT` : Déconnexion
- `CREATE_QUITUS` : Création d'un quitus
- `VIEW_QUITUS` : Consultation d'un quitus
- `EXPORT_PDF` : Téléchargement d'un PDF
- `EXPORT_CSV` : Export CSV
- `VERIFICATION` : Vérification d'un quitus
- `FAILED_LOGIN` : Tentative de connexion échouée
- `PERMISSION_DENIED` : Accès refusé
- `CUSTOM` : Actions personnalisées (changement de mot de passe, etc.)

## 🎨 Interface

### Filtres (en haut de page)

```
┌─────────────────────────────────────────────────────────┐
│ Filtres                                                  │
│ ┌──────────┬────────┬─────────┬──────────┬────────┬───┐ │
│ │Utilisateur│ Action │ N° Quitus│ Date début│ Date fin│🔍│ │
│ └──────────┴────────┴─────────┴──────────┴────────┴───┘ │
└─────────────────────────────────────────────────────────┘
```

**Note** : Le champ "Utilisateur" n'apparaît que pour les admins/chefs.

### Tableau des logs

Pour **Admins/Chefs** :
```
┌──────────────┬──────────┬────────────┬──────────┬──────────┬─────────┐
│ Date         │ Action   │ Utilisateur│ Quitus   │ IP       │ Détails │
├──────────────┼──────────┼────────────┼──────────┼──────────┼─────────┤
│ 10/11 14:30  │ LOGIN    │ marcel     │ -        │ 127.0.0.1│ Conn... │
│ 10/11 14:35  │ CREATE...│ jdupont    │ PAL-001  │ 192....  │ Quitus..│
└──────────────┴──────────┴────────────┴──────────┴──────────┴─────────┘
```

Pour **Agents** :
```
┌──────────────┬──────────┬──────────┬──────────┬─────────┐
│ Date         │ Action   │ Quitus   │ IP       │ Détails │
├──────────────┼──────────┼──────────┼──────────┼─────────┤
│ 10/11 14:30  │ LOGIN    │ -        │ 127.0.0.1│ Conn... │
│ 10/11 14:35  │ CREATE...│ PAL-001  │ 192....  │ Quitus..│
└──────────────┴──────────┴──────────┴──────────┴─────────┘
```

## 💡 Cas d'usage

### Agent consultant son historique
```
1. Agent "Jean Dupont" se connecte
2. Clique sur "Historique" dans la navbar
3. Voit uniquement ses propres actions
4. Peut filtrer par :
   - Type d'action (ex: voir seulement les créations de quitus)
   - Numéro de quitus (ex: retrouver toutes les actions sur PAL-2024-001)
   - Date (ex: actions du mois dernier)
```

### Admin surveillant l'activité
```
1. Admin "Marcel KOKOU" se connecte
2. Clique sur "Historique" dans la navbar
3. Voit TOUTES les actions de TOUS les utilisateurs
4. Peut filtrer par :
   - Utilisateur spécifique (ex: voir ce que "jdupont" a fait)
   - Type d'action (ex: voir tous les téléchargements PDF)
   - Numéro de quitus (ex: qui a consulté PAL-2024-001)
   - Date (ex: activité d'hier)
```

### Chef vérifiant les connexions échouées
```
1. Chef se connecte
2. Va sur "Historique"
3. Filtre par action : "FAILED_LOGIN"
4. Voit toutes les tentatives de connexion échouées
5. Peut identifier :
   - Qui tente de se connecter sans succès
   - Depuis quelle IP
   - À quelle fréquence (possible attaque)
```

## 🔒 Sécurité et Permissions

### Qui peut voir quoi ?

| Rôle | Vue | Filtres disponibles | Peut voir les autres utilisateurs ? |
|------|-----|---------------------|-------------------------------------|
| **Agent** | Ses propres logs uniquement | Action, Quitus, Date | ❌ Non |
| **Chef/Directeur** | Tous les logs | Utilisateur, Action, Quitus, Date | ✅ Oui |
| **Admin Plateforme** | Tous les logs | Utilisateur, Action, Quitus, Date | ✅ Oui |

### Protection des données

- ✅ Filtrage automatique basé sur `request.user.is_staff` et `request.user.is_superuser`
- ✅ Les agents ne peuvent PAS voir les actions des autres, même en modifiant l'URL
- ✅ Message clair pour les agents : "Vue restreinte"
- ✅ Décorateur `@login_required` : connexion obligatoire

## 🛠️ Implémentation technique

### Vue (`views.py`)
```python
@login_required
def history_log(request):
    # Filtre automatique pour les non-staff
    if not (request.user.is_superuser or request.user.is_staff):
        qs = qs.filter(utilisateur=request.user.username)
    
    # Pagination (25 par page)
    # Filtres (action, quitus, dates)
    # ...
```

### Template (`history.html`)
```django
{% if is_restricted %}
<div class="alert alert-info">
    Vue restreinte : Vous voyez uniquement vos propres actions.
</div>
{% endif %}

<!-- Colonne utilisateur conditionnelle -->
{% if not is_restricted %}
<th>Utilisateur</th>
{% endif %}
```

### Route (`urls.py`)
```python
path('history/', views.history_log, name='history_log'),
```

## 📊 Données affichées

Pour chaque entrée de log :

| Champ | Description | Exemple |
|-------|-------------|---------|
| **Date** | Date et heure de l'action | 10/11/2025 14:30 |
| **Action** | Type d'action effectuée | CREATE_QUITUS |
| **Utilisateur** | Nom d'utilisateur (admin/chef seulement) | marcel |
| **Quitus** | Lien vers le quitus concerné | PAL-2024-001 |
| **IP** | Adresse IP de l'utilisateur | 192.168.1.10 |
| **Détails** | Informations supplémentaires | Quitus créé - Bénéficiaire: ... |

## 🚀 Utilisation recommandée

### Pour les Agents
- Consultez régulièrement votre historique pour vérifier vos actions
- Utilisez les filtres par date pour retrouver des actions anciennes
- Cliquez sur les numéros de quitus pour accéder directement au détail

### Pour les Chefs/Admins
- **Audit quotidien** : Vérifiez les actions sensibles (suppressions, modifications)
- **Surveillance des connexions** : Filtrez par `FAILED_LOGIN` pour détecter les tentatives d'intrusion
- **Traçabilité** : Utilisez le filtre utilisateur pour suivre l'activité d'un agent spécifique
- **Rapports** : Filtrez par date et action pour générer des statistiques

## 🔄 Pagination

- **25 entrées par page** pour des temps de chargement rapides
- Boutons de navigation : "◀ Préc" et "Suiv ▶"
- Indicateur de page actuelle : "Page 1 / 10"
- Les filtres sont conservés lors de la navigation entre les pages

## ⚠️ Limitations actuelles

- Pas d'export CSV/Excel directement depuis l'historique (pourrait être ajouté)
- Pas de recherche en texte libre dans les détails
- Pas de tri par colonne (ordre chronologique inverse uniquement)

## 🎯 Améliorations futures possibles

1. **Export** : Bouton pour exporter les logs filtrés en CSV/Excel
2. **Graphiques** : Visualisation de l'activité par jour/semaine
3. **Recherche avancée** : Recherche dans les détails
4. **Notifications** : Alertes pour actions suspectes
5. **Statistiques** : Nombre d'actions par type, par utilisateur, etc.

## 📝 Notes importantes

- Les logs sont stockés de manière permanente dans la table `HistoriqueQuitus`
- Chaque action importante est automatiquement enregistrée via `AuditLogger`
- L'historique ne peut PAS être modifié ou supprimé par les utilisateurs
- Seuls les admins Django peuvent supprimer des entrées d'historique via l'admin

## 🆘 Dépannage

### "Aucun enregistrement trouvé"
- Vérifiez vos filtres (ils peuvent être trop restrictifs)
- Effacez les filtres et réessayez
- Pour les agents : vous n'avez peut-être pas encore effectué d'actions

### Les filtres ne fonctionnent pas
- Vérifiez le format de la date (utilisez le sélecteur de date)
- Les recherches sont insensibles à la casse
- Les filtres sont cumulatifs (plusieurs filtres = ET logique)

### La pagination ne fonctionne pas
- Vérifiez votre connexion internet
- Rafraîchissez la page
- Vérifiez la console du navigateur pour les erreurs

---

**Date de création** : 11 novembre 2025  
**Version** : 1.0  
**Statut** : ✅ Fonctionnel et testé

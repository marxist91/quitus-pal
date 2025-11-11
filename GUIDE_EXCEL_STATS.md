# Guide des Exports Excel et Statistiques Agents

## 📋 Vue d'Ensemble

Ce guide documente les fonctionnalités d'export Excel et le tableau de bord des statistiques agents ajoutées au système de gestion des quitus PAL.

## 🎯 Fonctionnalités

### 1. Export Excel des Quitus

**Accessible à :** Tous les utilisateurs authentifiés

**Accès :** 
- Page "Liste des Quitus" → Bouton "Exporter Excel" (vert)

**Fonctionnalités :**
- Export de tous les quitus en format `.xlsx`
- Respect des filtres de recherche appliqués
- Formatage professionnel avec en-têtes colorés
- Colonnes ajustées automatiquement

**Colonnes exportées :**
| Colonne | Description |
|---------|-------------|
| Numéro Quitus | Identifiant unique du quitus |
| Date Création | Date et heure de création (format DD/MM/YYYY HH:MM) |
| Bénéficiaire | Nom complet du bénéficiaire |
| NIF | Numéro d'Identification Fiscale |
| Téléphone | Numéro de téléphone du bénéficiaire |
| Email | Adresse email du bénéficiaire |
| Agent | Nom de l'agent ayant créé le quitus |
| Statut | Actif, Expiré, ou Annulé |
| Date de Validité | Date d'expiration du quitus |

**Format de fichier :** `quitus_export_YYYYMMDD_HHMMSS.xlsx`

**Style :**
- En-têtes : Fond bleu (#4472C4), texte blanc, gras
- Texte centré dans les en-têtes
- Largeurs de colonnes optimisées pour la lisibilité

---

### 2. Export Excel de l'Historique

**Accessible à :** Tous les utilisateurs authentifiés

**Accès :**
- Page "Historique" → Bouton "Exporter Excel" (vert, en haut à droite)

**Fonctionnalités :**
- Export des logs d'audit en format `.xlsx`
- **Respect des restrictions de rôle** :
  - Agents : Exportent uniquement leurs propres actions
  - Chefs/Admins : Exportent tout l'historique
- Respect de tous les filtres appliqués (utilisateur, action, quitus, dates)

**Colonnes exportées :**
| Colonne | Description |
|---------|-------------|
| Date & Heure | Date et heure de l'action (DD/MM/YYYY HH:MM:SS) |
| Action | Type d'action effectuée |
| Utilisateur | Nom d'utilisateur de l'auteur |
| Quitus | Numéro du quitus concerné (si applicable) |
| Adresse IP | IP de l'utilisateur |
| Détails | Description complète de l'action |

**Format de fichier :** `historique_export_YYYYMMDD_HHMMSS.xlsx`

**Style :**
- En-têtes : Fond vert (#70AD47), texte blanc, gras
- Colonne "Détails" extra-large (50 caractères) pour contenu complet

---

### 3. Tableau de Bord Statistiques Agents

**Accessible à :** Chefs de service et Administrateurs uniquement

**Accès :**
- Page d'accueil → Carte "Statistiques Agents" → Bouton "Voir Stats"
- URL directe : `/dashboard/stats/`

**Protection :**
- Décorateur `@role_required('admin_plateforme', 'admin_service')`
- Agents ordinaires redirigés avec message d'erreur

#### Cartes Récapitulatives

| Carte | Description |
|-------|-------------|
| **Total Agents** | Nombre d'agents actifs (ou tous si filtre activé) |
| **Total Quitus** | Somme des quitus sur la période sélectionnée |
| **Moyenne** | Nombre moyen de quitus par agent |
| **Plus Productif** | Nom et nombre de quitus de l'agent le plus actif |

#### Filtres Disponibles

**Période :**
- 7 derniers jours
- 30 derniers jours (défaut)
- 3 derniers mois
- 6 derniers mois
- 1 an
- Tout l'historique

**Affichage :**
- Agents actifs uniquement (défaut)
- Inclure les agents inactifs

#### Tableau Détaillé par Agent

**Colonnes :**
| Colonne | Description |
|---------|-------------|
| # | Numéro de classement |
| Agent | Nom complet de l'agent |
| Fonction | Poste occupé |
| Matricule | Numéro matricule |
| Total Quitus | Nombre total de quitus (badge bleu) |
| Actifs | Nombre de quitus actifs (badge vert) |
| Expirés | Nombre de quitus expirés (badge jaune) |
| Annulés | Nombre de quitus annulés (badge rouge) |
| Dernier Quitus | Date du dernier quitus créé |
| Statut | Actif ou Inactif |

**Tri :** Agents classés par nombre total de quitus (décroissant)

**Indication visuelle :** Agents inactifs affichés avec fond gris

#### Cartes Comparatives

Deux cartes en bas de page montrent :
- **Agent le Plus Productif** : Nom, fonction, total, répartition (actifs/expirés/annulés)
- **Agent le Moins Productif** : Mêmes informations (parmi ceux ayant au moins 1 quitus)

---

## 🔐 Permissions

| Fonctionnalité | Agent | Chef | Admin |
|----------------|-------|------|-------|
| Export Excel Quitus | ✅ | ✅ | ✅ |
| Export Excel Historique | ✅ (ses logs) | ✅ (tous) | ✅ (tous) |
| Statistiques Agents | ❌ | ✅ | ✅ |

---

## 📊 Cas d'Usage

### Pour les Agents
1. **Exporter ses quitus** pour analyse locale
2. **Exporter son historique** pour vérifier ses propres actions

### Pour les Chefs de Service
1. **Analyser la productivité** de l'équipe
2. **Identifier les agents sous-performants**
3. **Exporter des rapports complets** pour la direction
4. **Vérifier la répartition** des statuts de quitus par agent

### Pour les Administrateurs
1. **Auditer l'activité globale** du système
2. **Générer des rapports Excel** pour archivage
3. **Analyser les tendances** sur différentes périodes
4. **Comparer les performances** inter-services

---

## 🛠️ Implémentation Technique

### Fichiers Modifiés

**Backend :**
- `views.py` : Ajout de 3 vues (`export_quitus_excel`, `export_history_excel`, `dashboard_stats`)
- `urls.py` : Ajout de 3 routes
- `requirements.txt` : Ajout de `openpyxl`

**Frontend :**
- `liste.html` : Boutons CSV et Excel
- `history.html` : Bouton export Excel
- `accueil.html` : Carte "Statistiques Agents"
- `dashboard_stats.html` : **NOUVEAU** template complet

### Dépendances

```python
openpyxl  # Pour génération de fichiers Excel
```

Installation :
```bash
pip install -r requirements.txt
```

### Structure des Vues

#### export_quitus_excel
```python
@login_required
def export_quitus_excel(request):
    # Récupère quitus avec filtres
    # Crée workbook openpyxl
    # Style en-têtes (fond bleu, texte blanc)
    # Ajuste largeurs colonnes
    # Retourne fichier .xlsx
    # Log l'export via AuditLogger
```

#### export_history_excel
```python
@login_required
def export_history_excel(request):
    # Respecte restrictions de rôle (agent vs admin/chef)
    # Applique filtres (user, action, quitus, dates)
    # Crée workbook avec style vert
    # Retourne fichier .xlsx
    # Log l'export
```

#### dashboard_stats
```python
@login_required
@role_required('admin_plateforme', 'admin_service')
def dashboard_stats(request):
    # Filtre par période (7j, 30j, 90j, etc.)
    # Annotate agents avec Count() de quitus
    # Filtre par statut (actifs/inactifs)
    # Calcule stats globales (total, moyenne, min, max)
    # Récupère dernier quitus par agent
    # Retourne context avec agents_stats
```

### Optimisations

**Requêtes SQL :**
- `select_related('agent')` pour éviter N+1 queries
- `annotate()` avec `Count()` pour agrégation côté DB
- Filtres `Q()` combinés efficacement

**Mémoire :**
- Génération Excel en streaming (pas de fichier temporaire)
- Écriture directe dans HttpResponse

**Performance :**
- Pagination maintenue sur pages web (25 entrées)
- Exports Excel sans limite (toutes les données filtrées)

---

## 📝 Exemples d'Utilisation

### Exporter les quitus d'un agent spécifique
1. Aller sur "Liste des Quitus"
2. Rechercher le nom de l'agent dans la barre de recherche
3. Cliquer sur "Exporter Excel"
4. Le fichier contient uniquement les quitus filtrés

### Analyser la productivité sur 3 mois
1. Aller sur "Statistiques Agents" (chef/admin)
2. Sélectionner "3 derniers mois" dans le filtre période
3. Cliquer "Filtrer"
4. Consulter le tableau trié par performance

### Exporter l'historique d'une action spécifique
1. Aller sur "Historique"
2. Sélectionner l'action (ex: "CREATE_QUITUS")
3. Choisir une plage de dates
4. Cliquer "Exporter Excel"
5. Ouvrir le fichier pour analyse détaillée

---

## 🎨 Interface Utilisateur

### Codes Couleur

**Exports :**
- CSV : Vert clair (outline)
- Excel : Vert foncé (rempli)

**Statistiques :**
- Total Agents : Bleu (#007bff)
- Total Quitus : Vert (#28a745)
- Moyenne : Info (#17a2b8)
- Plus Productif : Jaune (#ffc107)

**Badges Statut :**
- Actifs : Vert
- Expirés : Jaune
- Annulés : Rouge
- Agent Inactif : Gris

### Responsive Design
- Cartes s'adaptent sur mobile (grid responsive)
- Tableau scrollable horizontalement
- En-têtes sticky pour tableaux longs

---

## 🔍 Débogage

### Vérifier l'installation d'openpyxl
```bash
pip show openpyxl
```

### Tester les vues
```bash
python manage.py check
```

### Logs d'export
Tous les exports sont enregistrés dans `HistoriqueQuitus` avec action `EXPORT_EXCEL`

### Problèmes courants

**Erreur : ModuleNotFoundError: No module named 'openpyxl'**
```bash
pip install openpyxl
```

**Permission refusée sur statistiques**
→ Vérifier `user.is_staff` ou `user.is_superuser`

**Export vide**
→ Vérifier les filtres appliqués

**Colonnes trop étroites**
→ Ajuster `column_widths` dans les vues

---

## 📈 Évolutions Futures

### Améliorations Possibles
- [ ] Export PDF multi-pages pour statistiques
- [ ] Graphiques dans Excel (via openpyxl charts)
- [ ] Export planifié automatique (celery)
- [ ] Comparaison période vs période
- [ ] Alertes sur baisse de productivité
- [ ] Export JSON/API pour intégration externe

### Graphiques Visuels
- [ ] Chart.js pour graphiques dans dashboard_stats.html
- [ ] Graphique en barres (quitus par agent)
- [ ] Graphique en camembert (statuts)
- [ ] Évolution temporelle (courbe)

---

## 🧪 Tests Recommandés

### Tests Fonctionnels
- [x] Export Excel quitus sans filtres
- [x] Export Excel quitus avec recherche
- [x] Export Excel historique (agent)
- [x] Export Excel historique (admin)
- [x] Statistiques avec période 30 jours
- [x] Statistiques tout l'historique
- [x] Filtre agents inactifs
- [x] Redirection si agent tente d'accéder aux stats

### Tests d'Intégration
- [ ] Ouvrir fichier Excel dans Microsoft Excel
- [ ] Ouvrir fichier Excel dans LibreOffice Calc
- [ ] Vérifier encodage UTF-8 (accents)
- [ ] Vérifier largeurs colonnes
- [ ] Vérifier couleurs en-têtes
- [ ] Vérifier calculs statistiques (compter manuellement)

### Tests de Performance
- [ ] Export de 1000+ quitus
- [ ] Export de 10000+ logs
- [ ] Statistiques avec 50+ agents
- [ ] Temps de génération < 5 secondes

---

## 📞 Support

**Questions techniques :**
- Consulter ce guide
- Vérifier `GUIDE_HISTORIQUE.md` pour contexte audit
- Examiner le code source (`views.py`)

**Bugs :**
- Vérifier les logs Django (`manage.py runserver`)
- Consulter `HistoriqueQuitus` pour logs d'export
- Utiliser `python manage.py check`

---

## 📚 Ressources

**Documentation Externe :**
- [openpyxl Documentation](https://openpyxl.readthedocs.io/)
- [Django Annotations](https://docs.djangoproject.com/en/5.0/topics/db/aggregation/)
- [Django Q Objects](https://docs.djangoproject.com/en/5.0/topics/db/queries/#complex-lookups-with-q-objects)

**Fichiers Connexes :**
- `GUIDE_HISTORIQUE.md` : Documentation de l'historique des actions
- `test_historique_feature.py` : Script de vérification
- `audit.py` : Système d'audit centralisé

---

**Date de création :** Janvier 2025  
**Dernière mise à jour :** Janvier 2025  
**Version :** 1.0  
**Auteur :** Équipe de développement PAL

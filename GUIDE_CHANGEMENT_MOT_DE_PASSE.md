# Guide - Gestion des Mots de Passe et Authentification

## 📋 Nouvelles Fonctionnalités Implémentées

### 1. **Authentification par Email** ✉️
Les utilisateurs peuvent maintenant se connecter avec leur **email** ou leur **nom d'utilisateur**.

**Comment ça marche :**
- Sur la page de connexion, entrez votre email (ex: `marcel@togoport.tg`) ou votre nom d'utilisateur
- Le système détecte automatiquement si c'est un email et trouve l'utilisateur correspondant
- Vous êtes connecté normalement

### 2. **Mot de Passe par Défaut** 🔐
Lorsqu'un Admin Plateforme ou Chef/Directeur crée un utilisateur, un mot de passe par défaut est automatiquement assigné si aucun mot de passe personnalisé n'est fourni.

**Mot de passe par défaut : `TogoPort2024@`**

**Comment créer un utilisateur :**
1. Aller sur le Dashboard Utilisateurs
2. Cliquer sur "Ajouter un utilisateur"
3. Remplir les informations (username, email, prénom, nom, rôle)
4. **Option 1 :** Laisser les champs "Mot de passe" vides → Le mot de passe par défaut `TogoPort2024@` sera assigné
5. **Option 2 :** Définir un mot de passe personnalisé (minimum 8 caractères)
6. Sauvegarder

**Note importante :** L'utilisateur recevra ses identifiants et pourra changer le mot de passe lors de sa première connexion ou à tout moment.

### 3. **Changement de Mot de Passe** 🔄

#### Pour l'utilisateur connecté :
1. Cliquez sur votre nom (en haut à droite dans la navbar)
2. Sélectionnez **"Changer le mot de passe"** dans le menu déroulant
3. Remplissez le formulaire :
   - **Mot de passe actuel** : Votre mot de passe actuel (ou `TogoPort2024@` si c'est votre première connexion)
   - **Nouveau mot de passe** : Votre nouveau mot de passe (minimum 8 caractères)
   - **Confirmer le nouveau mot de passe** : Retapez le nouveau mot de passe
4. Cliquez sur **"Changer le mot de passe"**
5. Vous restez connecté avec votre nouveau mot de passe

#### Exigences du mot de passe :
- ✅ Au moins 8 caractères
- ✅ Évitez d'utiliser des informations personnelles évidentes
- ✅ Recommandé : combinaison de lettres, chiffres et symboles

### 4. **Affichage du Nom Complet dans la Navbar** 👤
La navbar affiche maintenant le **prénom et nom** de l'utilisateur connecté au lieu du nom d'utilisateur.

**Logique d'affichage :**
- Si prénom ET nom sont renseignés : `Prénom Nom` (ex: "Marcel KOKOU")
- Si seulement le prénom est renseigné : `Prénom` (ex: "Marcel")
- Sinon : `username` (ex: "marcel")

## 🎯 Scénarios d'Utilisation

### Scénario 1 : Première connexion d'un nouvel utilisateur

1. **L'admin crée l'utilisateur :**
   - Username : `jdupont`
   - Email : `jdupont@togoport.tg`
   - Prénom : `Jean`
   - Nom : `Dupont`
   - Rôle : `Agent`
   - Mot de passe : *(laissé vide)*
   
2. **Le système assigne automatiquement le mot de passe par défaut :** `TogoPort2024@`

3. **L'admin communique les identifiants à Jean :**
   - Email/Username : `jdupont@togoport.tg` ou `jdupont`
   - Mot de passe : `TogoPort2024@`

4. **Jean se connecte pour la première fois :**
   - Va sur la page de connexion
   - Entre son email : `jdupont@togoport.tg`
   - Entre le mot de passe : `TogoPort2024@`
   - Clique sur "Se Connecter"

5. **Jean change immédiatement son mot de passe :**
   - Clique sur son nom "Jean Dupont" dans la navbar
   - Sélectionne "Changer le mot de passe"
   - Entre son mot de passe actuel : `TogoPort2024@`
   - Entre son nouveau mot de passe sécurisé
   - Confirme le nouveau mot de passe
   - Valide

6. **Jean est maintenant configuré avec son propre mot de passe !** ✅

### Scénario 2 : Admin définit un mot de passe personnalisé

1. **L'admin crée l'utilisateur avec un mot de passe personnalisé :**
   - Remplit les informations de base
   - Entre un mot de passe dans "Mot de passe" : `MonMotDePasse2024!`
   - Confirme dans "Confirmer le mot de passe"
   - Sauvegarde

2. **L'utilisateur reçoit ce mot de passe personnalisé**
3. **Il peut le changer quand il le souhaite**

### Scénario 3 : Changement périodique du mot de passe

1. **L'utilisateur souhaite changer son mot de passe :**
   - Clique sur son nom dans la navbar
   - Sélectionne "Changer le mot de passe"
   - Entre son mot de passe actuel
   - Définit son nouveau mot de passe
   - Confirme
   - Valide

2. **Le système met à jour le mot de passe et maintient la session active**

## 🔒 Sécurité

### Mesures de sécurité implémentées :

1. **Validation du mot de passe :**
   - Vérification de l'ancien mot de passe avant changement
   - Longueur minimale de 8 caractères
   - Confirmation du nouveau mot de passe

2. **Session maintenue après changement :**
   - L'utilisateur n'est pas déconnecté après avoir changé son mot de passe
   - La session est automatiquement mise à jour

3. **Authentification flexible :**
   - Connexion par email ou username
   - Protection contre les tentatives non autorisées

4. **Audit des changements :**
   - Tous les changements de mot de passe sont enregistrés dans l'audit log
   - Traçabilité complète des actions

## 📝 Notes Techniques

### Fichiers modifiés :

1. **`forms.py`** :
   - `LoginForm` : Authentification par email ajoutée
   - `UserRoleForm` : Mot de passe optionnel avec défaut `TogoPort2024@`
   - `PasswordChangeForm` : Nouveau formulaire pour changement de mot de passe

2. **`views.py`** :
   - `change_password` : Nouvelle vue pour gérer le changement de mot de passe
   - Utilise `update_session_auth_hash` pour maintenir la session active

3. **`urls.py`** :
   - Route ajoutée : `path('change-password/', views.change_password, name='change_password')`

4. **`templates/base.html`** :
   - Navbar mise à jour pour afficher prénom + nom
   - Menu dropdown avec lien "Changer le mot de passe"
   - Admin Django visible uniquement pour superusers

5. **`templates/change_password.html`** :
   - Nouveau template pour le changement de mot de passe
   - Interface utilisateur intuitive avec validation JS

6. **`templates/user_form.html`** :
   - Info box ajoutée pour expliquer le mot de passe par défaut
   - Champs de mot de passe marqués comme optionnels

7. **`templates/login.html`** :
   - Message mis à jour pour indiquer qu'on peut se connecter avec l'email

## 🎓 Bonnes Pratiques

### Pour les Administrateurs :

1. **Communication des identifiants :**
   - Toujours communiquer les identifiants de manière sécurisée
   - Encourager l'utilisateur à changer le mot de passe par défaut dès la première connexion

2. **Gestion des utilisateurs :**
   - Utiliser le Dashboard Utilisateurs au lieu de l'admin Django
   - Assigner les rôles appropriés (Admin, Chef, Agent)
   - Désactiver les comptes inutilisés au lieu de les supprimer

### Pour les Utilisateurs :

1. **Mot de passe sécurisé :**
   - Utilisez au moins 8 caractères
   - Mélangez lettres (majuscules/minuscules), chiffres et symboles
   - Évitez les informations personnelles

2. **Changement régulier :**
   - Changez votre mot de passe régulièrement
   - Ne partagez jamais votre mot de passe

3. **Sécurité de connexion :**
   - Déconnectez-vous toujours après utilisation
   - Vérifiez que vous êtes sur un ordinateur sécurisé

## ❓ FAQ

**Q : Que faire si j'ai oublié mon mot de passe ?**
R : Contactez un administrateur qui pourra réinitialiser votre mot de passe au mot de passe par défaut `TogoPort2024@`.

**Q : Puis-je me connecter avec mon email ?**
R : Oui ! Vous pouvez utiliser soit votre email, soit votre nom d'utilisateur pour vous connecter.

**Q : Le mot de passe par défaut est-il sécurisé ?**
R : Le mot de passe par défaut `TogoPort2024@` est temporaire. Il est **fortement recommandé** de le changer dès la première connexion.

**Q : Que se passe-t-il si je me trompe dans mon mot de passe actuel ?**
R : Le formulaire affichera une erreur et vous devrez entrer le bon mot de passe actuel pour continuer.

**Q : Puis-je changer mon mot de passe plusieurs fois ?**
R : Oui, vous pouvez changer votre mot de passe autant de fois que vous le souhaitez.

---

**Dernière mise à jour :** 10 novembre 2025
**Version :** 1.0

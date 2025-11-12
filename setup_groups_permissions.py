"""
Script pour créer et configurer les groupes et permissions Django
pour le système de gestion de quitus.

Trois rôles:
1. Agent (Simple utilisateur) - Crée et gère ses propres quitus
2. Chef_Directeur - Gestion complète + statistiques + création utilisateurs
3. Superuser (Admin plateforme) - Accès total

Usage:
    python setup_groups_permissions.py
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_quitus_PAL.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from quitus_app.models import Quitus, HistoriqueQuitus, UserProfile, HistoriqueNotifications

def create_groups_and_permissions():
    """Créer les groupes et assigner les permissions"""
    
    print("🔧 Configuration des groupes et permissions...\n")
    
    # ========================================
    # 1. GROUPE: Agent (Simple Utilisateur)
    # ========================================
    agent_group, created = Group.objects.get_or_create(name='Agent')
    if created:
        print("✅ Groupe 'Agent' créé")
    else:
        print("ℹ️  Groupe 'Agent' existe déjà")
    
    # Permissions pour Agent
    agent_permissions = [
        # Quitus - Peut créer et voir ses propres quitus
        ('add_quitus', 'quitus_app', 'quitus'),
        ('view_quitus', 'quitus_app', 'quitus'),
        
        # Historique - Consultation seulement
        ('view_historiquequitus', 'quitus_app', 'historiquequitus'),
        
        # Notifications - Envoi et consultation
        ('add_historiquenotifications', 'quitus_app', 'historiquenotifications'),
        ('view_historiquenotifications', 'quitus_app', 'historiquenotifications'),
        
        # UserProfile - Vue seulement
        ('view_userprofile', 'quitus_app', 'userprofile'),
    ]
    
    agent_perms = []
    for codename, app_label, model in agent_permissions:
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model)
            perm = Permission.objects.get(content_type=content_type, codename=codename)
            agent_perms.append(perm)
        except Permission.DoesNotExist:
            print(f"⚠️  Permission {codename} non trouvée pour {model}")
    
    agent_group.permissions.set(agent_perms)
    print(f"   → {len(agent_perms)} permissions assignées aux Agents\n")
    
    # ========================================
    # 2. GROUPE: Chef_Directeur
    # ========================================
    chef_group, created = Group.objects.get_or_create(name='Chef_Directeur')
    if created:
        print("✅ Groupe 'Chef_Directeur' créé")
    else:
        print("ℹ️  Groupe 'Chef_Directeur' existe déjà")
    
    # Permissions pour Chef_Directeur (toutes sauf delete user)
    chef_permissions = [
        # Quitus - Gestion complète
        ('add_quitus', 'quitus_app', 'quitus'),
        ('change_quitus', 'quitus_app', 'quitus'),
        ('delete_quitus', 'quitus_app', 'quitus'),
        ('view_quitus', 'quitus_app', 'quitus'),
        
        # Historique - Consultation complète
        ('view_historiquequitus', 'quitus_app', 'historiquequitus'),
        ('add_historiquequitus', 'quitus_app', 'historiquequitus'),
        
        # Notifications - Gestion complète
        ('add_historiquenotifications', 'quitus_app', 'historiquenotifications'),
        ('change_historiquenotifications', 'quitus_app', 'historiquenotifications'),
        ('view_historiquenotifications', 'quitus_app', 'historiquenotifications'),
        
        # UserProfile - Gestion complète
        ('add_userprofile', 'quitus_app', 'userprofile'),
        ('change_userprofile', 'quitus_app', 'userprofile'),
        ('view_userprofile', 'quitus_app', 'userprofile'),
        
        # Users - Création et modification (pas suppression)
        ('add_user', 'auth', 'user'),
        ('change_user', 'auth', 'user'),
        ('view_user', 'auth', 'user'),
        
        # Groups - Vue seulement
        ('view_group', 'auth', 'group'),
    ]
    
    chef_perms = []
    for codename, app_label, model in chef_permissions:
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model)
            perm = Permission.objects.get(content_type=content_type, codename=codename)
            chef_perms.append(perm)
        except Permission.DoesNotExist:
            print(f"⚠️  Permission {codename} non trouvée pour {model}")
    
    chef_group.permissions.set(chef_perms)
    print(f"   → {len(chef_perms)} permissions assignées aux Chef_Directeur\n")
    
    # ========================================
    # 3. SUPERUSER (Admin Plateforme)
    # ========================================
    print("✅ Superuser (Admin Plateforme)")
    print("   → Accès total via is_superuser=True (pas de groupe nécessaire)\n")
    
    # ========================================
    # Résumé
    # ========================================
    print("=" * 60)
    print("📋 RÉSUMÉ DES PERMISSIONS")
    print("=" * 60)
    
    print("\n🔵 AGENT (Simple Utilisateur):")
    print("   ✓ Créer des quitus")
    print("   ✓ Voir ses propres quitus")
    print("   ✓ Envoyer des notifications")
    print("   ✓ Consulter l'historique de ses quitus")
    print("   ✗ Modifier/Supprimer des quitus")
    print("   ✗ Voir les quitus des autres")
    print("   ✗ Accès aux statistiques")
    print("   ✗ Créer des utilisateurs")
    
    print("\n🟢 CHEF_DIRECTEUR:")
    print("   ✓ Toutes les permissions Agent +")
    print("   ✓ Modifier/Supprimer tous les quitus")
    print("   ✓ Voir tous les quitus")
    print("   ✓ Accès aux statistiques et dashboard")
    print("   ✓ Créer et modifier des utilisateurs")
    print("   ✓ Gérer les UserProfile")
    print("   ✓ Voir tous les historiques")
    print("   ✗ Supprimer des utilisateurs")
    print("   ✗ Modifier les permissions système")
    
    print("\n🔴 SUPERUSER (Admin Plateforme):")
    print("   ✓ Accès TOTAL à toutes les fonctionnalités")
    print("   ✓ Gestion complète Django Admin")
    print("   ✓ Suppression d'utilisateurs")
    print("   ✓ Modification des groupes et permissions")
    print("   ✓ Accès à tous les modèles système")
    
    print("\n" + "=" * 60)
    print("✅ Configuration terminée avec succès!")
    print("=" * 60)
    
    return agent_group, chef_group


def assign_user_to_group(username, group_name):
    """Assigner un utilisateur à un groupe"""
    from django.contrib.auth.models import User
    
    try:
        user = User.objects.get(username=username)
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        print(f"✅ Utilisateur '{username}' ajouté au groupe '{group_name}'")
    except User.DoesNotExist:
        print(f"❌ Utilisateur '{username}' non trouvé")
    except Group.DoesNotExist:
        print(f"❌ Groupe '{group_name}' non trouvé")


def list_users_and_groups():
    """Afficher tous les utilisateurs et leurs groupes"""
    from django.contrib.auth.models import User
    
    print("\n📊 UTILISATEURS ET LEURS RÔLES:")
    print("=" * 60)
    
    users = User.objects.all().order_by('username')
    for user in users:
        role = "🔴 SUPERUSER" if user.is_superuser else ""
        if not role:
            groups = user.groups.all()
            if groups:
                role = f"🟢 {groups[0].name}" if groups[0].name == 'Chef_Directeur' else f"🔵 {groups[0].name}"
            else:
                role = "⚪ Aucun groupe"
        
        status = "✓ Actif" if user.is_active else "✗ Inactif"
        print(f"{user.username:<20} {role:<30} {status}")
    
    print("=" * 60)


if __name__ == '__main__':
    # Créer les groupes et permissions
    agent_group, chef_group = create_groups_and_permissions()
    
    # Afficher les utilisateurs existants
    list_users_and_groups()
    
    print("\n💡 POUR ASSIGNER UN UTILISATEUR À UN GROUPE:")
    print("   Depuis Django Admin: Utilisateurs → Groupes")
    print("   Ou depuis ce script: assign_user_to_group('username', 'Agent')")

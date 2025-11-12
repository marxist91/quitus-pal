"""
Commande Django pour créer et configurer les groupes et permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Configure les groupes et permissions pour Agent, Chef_Directeur et Superuser'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('🔧 Configuration des groupes et permissions...\n'))
        
        # Créer les groupes
        agent_group = self.create_agent_group()
        chef_group = self.create_chef_directeur_group()
        
        # Afficher le résumé
        self.show_summary()
        
        # Afficher les utilisateurs
        self.list_users()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Configuration terminée avec succès!'))

    def create_agent_group(self):
        """Créer le groupe Agent avec ses permissions"""
        agent_group, created = Group.objects.get_or_create(name='Agent')
        
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Groupe "Agent" créé'))
        else:
            self.stdout.write('ℹ️  Groupe "Agent" existe déjà')
        
        # Permissions pour Agent
        permissions_codenames = [
            # Quitus
            'add_quitus',
            'view_quitus',
            # Historique
            'view_historiquequitus',
            # Notifications
            'add_historiquenotifications',
            'view_historiquenotifications',
            # UserProfile
            'view_userprofile',
        ]
        
        perms = Permission.objects.filter(
            codename__in=permissions_codenames,
            content_type__app_label='quitus_app'
        )
        
        agent_group.permissions.set(perms)
        self.stdout.write(f'   → {perms.count()} permissions assignées aux Agents\n')
        
        return agent_group

    def create_chef_directeur_group(self):
        """Créer le groupe Chef_Directeur avec ses permissions"""
        chef_group, created = Group.objects.get_or_create(name='Chef_Directeur')
        
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Groupe "Chef_Directeur" créé'))
        else:
            self.stdout.write('ℹ️  Groupe "Chef_Directeur" existe déjà')
        
        # Permissions pour Chef_Directeur
        app_permissions = Permission.objects.filter(
            content_type__app_label='quitus_app'
        )
        
        # Permissions auth (User, Group)
        auth_permissions = Permission.objects.filter(
            content_type__app_label='auth',
            codename__in=['add_user', 'change_user', 'view_user', 'view_group']
        )
        
        all_perms = list(app_permissions) + list(auth_permissions)
        chef_group.permissions.set(all_perms)
        
        self.stdout.write(f'   → {len(all_perms)} permissions assignées aux Chef_Directeur\n')
        
        return chef_group

    def show_summary(self):
        """Afficher le résumé des permissions"""
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.WARNING('📋 RÉSUMÉ DES PERMISSIONS'))
        self.stdout.write('=' * 60)
        
        self.stdout.write(self.style.HTTP_INFO('\n🔵 AGENT (Simple Utilisateur):'))
        self.stdout.write('   ✓ Créer des quitus')
        self.stdout.write('   ✓ Voir ses propres quitus')
        self.stdout.write('   ✓ Envoyer des notifications')
        self.stdout.write('   ✓ Consulter l\'historique de ses quitus')
        self.stdout.write('   ✗ Modifier/Supprimer des quitus')
        self.stdout.write('   ✗ Voir les quitus des autres')
        self.stdout.write('   ✗ Accès aux statistiques')
        
        self.stdout.write(self.style.HTTP_SUCCESS('\n🟢 CHEF_DIRECTEUR:'))
        self.stdout.write('   ✓ Toutes les permissions Agent +')
        self.stdout.write('   ✓ Modifier/Supprimer tous les quitus')
        self.stdout.write('   ✓ Voir tous les quitus')
        self.stdout.write('   ✓ Accès aux statistiques')
        self.stdout.write('   ✓ Créer et modifier des utilisateurs')
        self.stdout.write('   ✓ Gérer les UserProfile')
        
        self.stdout.write(self.style.ERROR('\n🔴 SUPERUSER (Admin Plateforme):'))
        self.stdout.write('   ✓ Accès TOTAL à toutes les fonctionnalités')
        self.stdout.write('   ✓ Gestion complète Django Admin')
        self.stdout.write('   ✓ Suppression d\'utilisateurs')
        self.stdout.write('   ✓ Modification des groupes et permissions')

    def list_users(self):
        """Afficher tous les utilisateurs et leurs rôles"""
        self.stdout.write('\n📊 UTILISATEURS ET LEURS RÔLES:')
        self.stdout.write('=' * 60)
        
        users = User.objects.all().order_by('username')
        for user in users:
            if user.is_superuser:
                role = self.style.ERROR('🔴 SUPERUSER')
            else:
                groups = user.groups.all()
                if groups.filter(name='Chef_Directeur').exists():
                    role = self.style.SUCCESS('🟢 Chef_Directeur')
                elif groups.filter(name='Agent').exists():
                    role = self.style.HTTP_INFO('🔵 Agent')
                else:
                    role = self.style.WARNING('⚪ Aucun groupe')
            
            status = '✓ Actif' if user.is_active else '✗ Inactif'
            self.stdout.write(f'{user.username:<20} {role:<40} {status}')
        
        self.stdout.write('=' * 60)

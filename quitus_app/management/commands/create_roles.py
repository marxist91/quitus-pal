from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from quitus_app.models import Quitus


class Command(BaseCommand):
    help = 'Crée les rôles et permissions pour la gestion des quitus'

    def handle(self, *args, **options):
        # Définir les trois rôles
        roles = {
            'Superuser': {
                'description': 'Admin plateforme - Accès total',
                'permissions': ['add_quitus', 'change_quitus', 'delete_quitus', 'view_quitus',
                              'add_agent', 'change_agent', 'delete_agent', 'view_agent',
                              'add_historiquequitus', 'change_historiquequitus', 'delete_historiquequitus', 'view_historiquequitus']
            },
            'Chef_Directeur': {
                'description': 'Chef/Directeur - Gestion du service',
                'permissions': ['add_quitus', 'change_quitus', 'view_quitus',
                              'view_agent', 'add_historiquequitus', 'view_historiquequitus']
            },
            'Agent': {
                'description': 'Agent - Créer et vérifier quitus',
                'permissions': ['add_quitus', 'change_quitus', 'view_quitus', 'view_historiquequitus']
            }
        }

        quitus_content_type = ContentType.objects.get_for_model(Quitus)

        for role_name, role_data in roles.items():
            group, created = Group.objects.get_or_create(name=role_name)
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Groupe créé: {role_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'→ Groupe existant: {role_name}'))
            
            # Ajouter les permissions au groupe
            permissions = []
            for perm_codename in role_data['permissions']:
                try:
                    perm = Permission.objects.get(content_type=quitus_content_type, codename=perm_codename)
                    permissions.append(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  ⚠ Permission non trouvée: {perm_codename}'))
            
            group.permissions.set(permissions)
            self.stdout.write(f'  → {len(permissions)} permissions assignées')

        self.stdout.write(self.style.SUCCESS('\n✓ Rôles et permissions créés avec succès!'))
        self.stdout.write('\nRôles disponibles:')
        for role_name, role_data in roles.items():
            self.stdout.write(f'  • {role_name}: {role_data["description"]}')

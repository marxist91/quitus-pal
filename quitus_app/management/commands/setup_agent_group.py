from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User

class Command(BaseCommand):
    help = "Vérifie et crée le groupe 'Agent' avec la permission de créer un quitus, puis ajoute un utilisateur à ce groupe."

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Nom d’utilisateur à ajouter au groupe Agent')

    def handle(self, *args, **options):
        # Vérifier/créer le groupe Agent
        group, created = Group.objects.get_or_create(name='Agent')
        if created:
            self.stdout.write(self.style.SUCCESS("Groupe 'Agent' créé."))
        else:
            self.stdout.write("Groupe 'Agent' déjà existant.")

        # Ajouter la permission add_quitus au groupe
        perm = Permission.objects.filter(codename='add_quitus').first()
        if perm:
            group.permissions.add(perm)
            self.stdout.write("Permission 'add_quitus' ajoutée au groupe Agent.")
        else:
            self.stdout.write(self.style.ERROR("Permission 'add_quitus' introuvable. Vérifiez vos migrations."))

        # Ajouter l’utilisateur au groupe si précisé
        username = options.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
                user.groups.add(group)
                self.stdout.write(self.style.SUCCESS(f"Utilisateur '{username}' ajouté au groupe Agent."))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Utilisateur '{username}' introuvable."))
        else:
            self.stdout.write("Aucun utilisateur précisé. Utilisez --username pour ajouter un utilisateur au groupe.")

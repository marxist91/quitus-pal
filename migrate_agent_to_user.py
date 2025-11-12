"""
Script de migration des données Agent vers User/UserProfile
Transfère les quitus de Agent vers User
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_quitus_PAL.settings')
django.setup()

from quitus_app.models import Agent, Quitus, UserProfile
from django.contrib.auth.models import User

print("="*80)
print("MIGRATION DES DONNÉES AGENT → USER/USERPROFILE")
print("="*80)

# Étape 1: Créer les profils pour les utilisateurs existants
print("\n[1] Création des profils utilisateurs...")
users = User.objects.all()
for user in users:
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'matricule': f'USR-{user.id}',
            'fonction': 'Agent',
            'telephone': '+228 00 00 00 00',
            'actif': True
        }
    )
    if created:
        print(f"   ✓ Profil créé pour {user.username}")
    else:
        print(f"   ℹ️ Profil existe déjà pour {user.username}")

# Étape 2: Associer les agents aux utilisateurs et migrer les quitus
print("\n[2] Association Agent → User et migration des quitus...")
agents = Agent.objects.all()

for agent in agents:
    print(f"\n   Agent: {agent.nom_complet} ({agent.email})")
    
    # Chercher l'utilisateur correspondant
    # Stratégie 1: Par matricule USR-X
    matricule_parts = agent.matricule.split('-')
    user = None
    
    if len(matricule_parts) == 2 and matricule_parts[0] == 'USR':
        try:
            user_id = int(matricule_parts[1])
            user = User.objects.get(id=user_id)
            print(f"     → Trouvé par matricule: {user.username}")
        except (ValueError, User.DoesNotExist):
            pass
    
    # Stratégie 2: Par email
    if not user:
        try:
            user = User.objects.get(email=agent.email)
            print(f"     → Trouvé par email: {user.username}")
        except User.DoesNotExist:
            print(f"     ⚠️ Utilisateur non trouvé pour {agent.email}")
            continue
    
    # Mettre à jour le profil de l'utilisateur avec les données de l'agent
    if hasattr(user, 'profile'):
        profile = user.profile
        profile.matricule = agent.matricule
        profile.fonction = agent.fonction
        profile.telephone = agent.telephone
        profile.actif = agent.actif
        profile.save()
        print(f"     ✓ Profil mis à jour")
    
    # Migrer tous les quitus de cet agent vers l'utilisateur
    quitus_list = Quitus.objects.filter(agent=agent)
    count = quitus_list.count()
    
    if count > 0:
        quitus_list.update(created_by=user)
        print(f"     ✓ {count} quitus migrés vers {user.username}")
    else:
        print(f"     ℹ️ Aucun quitus à migrer")

# Étape 3: Vérifier qu'il ne reste plus de quitus sans created_by
print("\n[3] Vérification des quitus sans utilisateur...")
orphan_quitus = Quitus.objects.filter(created_by__isnull=True)
count = orphan_quitus.count()

if count > 0:
    print(f"   ⚠️ {count} quitus sans utilisateur trouvés")
    for quitus in orphan_quitus[:10]:  # Afficher les 10 premiers
        print(f"      - {quitus.numero_quitus} (Agent: {quitus.agent})")
else:
    print(f"   ✓ Tous les quitus ont un utilisateur assigné")

# Étape 4: Résumé
print("\n" + "="*80)
print("RÉSUMÉ DE LA MIGRATION")
print("="*80)

print(f"\n✓ Utilisateurs: {User.objects.count()}")
print(f"✓ Profils créés: {UserProfile.objects.count()}")
print(f"✓ Agents dans la base: {Agent.objects.count()}")
print(f"✓ Quitus avec created_by: {Quitus.objects.filter(created_by__isnull=False).count()}")
print(f"✓ Quitus sans created_by: {Quitus.objects.filter(created_by__isnull=True).count()}")

print("\n" + "="*80)
print("MIGRATION TERMINÉE")
print("="*80)
print("\nPROCHAINES ÉTAPES:")
print("1. Vérifier que tous les quitus ont un created_by")
print("2. Tester l'application")
print("3. Mettre à jour les vues et templates pour utiliser created_by au lieu de agent")
print("4. Supprimer le modèle Agent après confirmation que tout fonctionne")

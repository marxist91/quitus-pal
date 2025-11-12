"""
Script pour synchroniser les emails des agents avec leurs utilisateurs
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_quitus_PAL.settings')
django.setup()

from quitus_app.models import Agent
from django.contrib.auth.models import User

print("=== Synchronisation des emails agents <-> utilisateurs ===\n")

# Cas 1: petit (agent USR-3) -> mettre à jour son email
print("1. Mise à jour de l'agent 'petit KODJO'")
try:
    user_petit = User.objects.get(username='petit')
    agent_petit = Agent.objects.get(matricule='USR-3')
    
    print(f"   User email: {user_petit.email}")
    print(f"   Agent email actuel: {agent_petit.email}")
    print(f"   → Mise à jour...")
    
    agent_petit.email = user_petit.email
    agent_petit.save()
    print(f"   ✓ Agent email mis à jour: {agent_petit.email}\n")
except Exception as e:
    print(f"   ✗ Erreur: {e}\n")

# Cas 2: marcel (admin plateforme) -> créer un agent
print("2. Création agent pour 'marcel' (admin plateforme)")
try:
    user_marcel = User.objects.get(username='marcel')
    
    # Vérifier si un agent existe déjà
    agent, created = Agent.objects.get_or_create(
        email=user_marcel.email,
        defaults={
            'nom_complet': user_marcel.get_full_name() or user_marcel.username,
            'matricule': f'USR-{user_marcel.id}',
            'fonction': 'Administrateur Plateforme',
            'telephone': '+228 00 00 00 00',
            'actif': True
        }
    )
    
    if created:
        print(f"   ✓ Agent créé: {agent.nom_complet} | {agent.email}\n")
    else:
        print(f"   ℹ️ Agent existe déjà: {agent.nom_complet} | {agent.email}\n")
except Exception as e:
    print(f"   ✗ Erreur: {e}\n")

# Cas 3: paul (chef_directeur) -> créer un agent
print("3. Création agent pour 'paul' (chef_directeur)")
try:
    user_paul = User.objects.get(username='paul')
    
    # Vérifier si un agent existe déjà
    agent, created = Agent.objects.get_or_create(
        email=user_paul.email,
        defaults={
            'nom_complet': user_paul.get_full_name() or user_paul.username,
            'matricule': f'USR-{user_paul.id}',
            'fonction': 'Chef de Direction',
            'telephone': '+228 00 00 00 00',
            'actif': True
        }
    )
    
    if created:
        print(f"   ✓ Agent créé: {agent.nom_complet} | {agent.email}\n")
    else:
        print(f"   ℹ️ Agent existe déjà: {agent.nom_complet} | {agent.email}\n")
except Exception as e:
    print(f"   ✗ Erreur: {e}\n")

print("\n=== Résultat final ===\n")
all_agents = Agent.objects.all().order_by('id')
for agent in all_agents:
    from quitus_app.models import Quitus
    quitus_count = Quitus.objects.filter(agent=agent).count()
    print(f"ID {agent.id}: {agent.nom_complet} | Email: {agent.email} | Matricule: {agent.matricule} | {quitus_count} quitus")

print("\n✓ Synchronisation terminée !")

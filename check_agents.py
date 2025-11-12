"""
Script pour vérifier les agents dupliqués après changement d'email
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_quitus_PAL.settings')
django.setup()

from quitus_app.models import Agent, Quitus
from django.contrib.auth.models import User

print("=== Utilisateurs et leurs agents ===\n")

users = User.objects.all()
for user in users:
    print(f"👤 USER: {user.username} - Email: {user.email}")
    
    # Chercher les agents liés à cet utilisateur (par matricule USR-X ou par email)
    agents = Agent.objects.filter(matricule=f"USR-{user.id}")
    
    if agents.exists():
        for agent in agents:
            quitus_count = Quitus.objects.filter(agent=agent).count()
            print(f"   → Agent ID {agent.id}: {agent.nom_complet}")
            print(f"      Email: {agent.email}")
            print(f"      Matricule: {agent.matricule}")
            print(f"      Quitus liés: {quitus_count}")
    else:
        # Chercher par email
        agents_by_email = Agent.objects.filter(email=user.email)
        if agents_by_email.exists():
            for agent in agents_by_email:
                quitus_count = Quitus.objects.filter(agent=agent).count()
                print(f"   → Agent ID {agent.id}: {agent.nom_complet}")
                print(f"      Email: {agent.email}")
                print(f"      Matricule: {agent.matricule}")
                print(f"      Quitus liés: {quitus_count}")
        else:
            print(f"   ⚠️ Aucun agent trouvé pour cet utilisateur")
    
    print()

print("\n=== Tous les agents dans la base ===\n")
all_agents = Agent.objects.all().order_by('id')
for agent in all_agents:
    quitus_count = Quitus.objects.filter(agent=agent).count()
    print(f"ID {agent.id}: {agent.nom_complet} | Email: {agent.email} | Matricule: {agent.matricule} | {quitus_count} quitus")

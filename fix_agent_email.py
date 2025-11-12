"""
Script pour mettre à jour les quitus après changement d'email d'un agent
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_quitus_PAL.settings')
django.setup()

from quitus_app.models import Agent, Quitus

print("=== Agents dans la base ===")
agents = Agent.objects.all()
for agent in agents:
    print(f"ID: {agent.id}, Nom: {agent.nom_complet}, Email: {agent.email}, Matricule: {agent.matricule}")
    quitus_count = Quitus.objects.filter(agent=agent).count()
    print(f"  -> {quitus_count} quitus liés\n")

print("\n=== CORRECTION ===")
print("Entrez l'ID de l'ancien agent (celui qui n'a plus d'email correct) :")
old_agent_id = input("ID ancien agent : ").strip()

print("Entrez l'ID du nouvel agent (celui avec le bon email) :")
new_agent_id = input("ID nouveau agent : ").strip()

if old_agent_id and new_agent_id:
    try:
        old_agent = Agent.objects.get(id=old_agent_id)
        new_agent = Agent.objects.get(id=new_agent_id)
        
        quitus_to_update = Quitus.objects.filter(agent=old_agent)
        count = quitus_to_update.count()
        
        print(f"\n{count} quitus seront transférés de '{old_agent.nom_complet}' vers '{new_agent.nom_complet}'")
        confirm = input("Confirmer ? (oui/non) : ").strip().lower()
        
        if confirm == 'oui':
            quitus_to_update.update(agent=new_agent)
            print(f"✓ {count} quitus mis à jour avec succès !")
            
            # Option : supprimer l'ancien agent si plus de quitus
            if Quitus.objects.filter(agent=old_agent).count() == 0:
                delete_old = input(f"\nSupprimer l'ancien agent '{old_agent.nom_complet}' ? (oui/non) : ").strip().lower()
                if delete_old == 'oui':
                    old_agent.delete()
                    print(f"✓ Ancien agent supprimé")
        else:
            print("Opération annulée")
            
    except Agent.DoesNotExist as e:
        print(f"Erreur : Agent non trouvé - {e}")
else:
    print("IDs non fournis, opération annulée")

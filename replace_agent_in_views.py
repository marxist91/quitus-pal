"""
Script pour remplacer agent par created_by/user dans views.py
"""
import re

# Lire le fichier
with open('quitus_app/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Sauvegarder l'original
with open('quitus_app/views.py.backup', 'w', encoding='utf-8') as f:
    f.write(content)

print("Backup créé: views.py.backup")

# Remplacements
replacements = [
    # quitus.agent.nom_complet → quitus.created_by.get_full_name() or quitus.created_by.username
    (r'quitus\.agent\.nom_complet if quitus\.agent else \'\'', 
     'quitus.created_by.get_full_name() or quitus.created_by.username if quitus.created_by else \'\''),
    
    # quitus.agent.email → quitus.created_by.email
    (r'quitus\.agent\.email if quitus\.agent', 
     'quitus.created_by.email if quitus.created_by'),
    
    # str(quitus.agent) → str(quitus.created_by)
    (r'str\(quitus\.agent\)', 
     'str(quitus.created_by)'),
    
    # Agent.objects.get(email=request.user.email) → request.user
    (r'agent = Agent\.objects\.get\(email=request\.user\.email\)',
     '# Utiliser directement request.user au lieu de chercher un agent'),
    
    (r'agent = Agent\.objects\.get\(email=user\.email\)',
     '# Utiliser directement user au lieu de chercher un agent'),
    
    # quitus.agent != agent → quitus.created_by != request.user
    (r'if quitus\.agent != agent:',
     'if quitus.created_by != request.user:'),
    
    # Agent.objects.filter(...) → User.objects.filter(...)
    (r'agents_list = Agent\.objects\.filter\(actif=True\)\.order_by\(\'nom_complet\'\)',
     'users_list = User.objects.filter(is_active=True, profile__actif=True).select_related(\'profile\').order_by(\'last_name\', \'first_name\')'),
    
    # Agent.objects.annotate(...) → User.objects.annotate(...)
    (r'agents_stats = Agent\.objects\.annotate\(',
     'users_stats = User.objects.filter(profile__isnull=False).annotate('),
    
    # quitus_count=Count('quitus') → quitus_count=Count('quitus_crees')
    (r'quitus_count=Count\(\'quitus\'\)',
     'quitus_count=Count(\'quitus_crees\')'),
]

# Appliquer les remplacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Sauvegarder
with open('quitus_app/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✓ Remplacements effectués")
print("\nVérifiez views.py et views.py.backup pour vous assurer que tout est correct")
print("Si quelque chose ne va pas, restaurez avec: cp views.py.backup views.py")

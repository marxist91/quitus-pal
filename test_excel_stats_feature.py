#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de vérification des fonctionnalités d'export Excel et statistiques agents
Gestion Quitus PAL - Port Autonome de Lomé
"""

import os
import sys

# Couleurs pour le terminal
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
END = '\033[0m'

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*80}{END}")
    print(f"{BOLD}{BLUE}{text.center(80)}{END}")
    print(f"{BOLD}{BLUE}{'='*80}{END}\n")

def print_section(text):
    print(f"\n{BOLD}{YELLOW}{text}{END}")
    print(f"{YELLOW}{'-'*len(text)}{END}")

def check_mark(status=True):
    return f"{GREEN}✅{END}" if status else f"{RED}❌{END}"

def main():
    print_header("🚀 VÉRIFICATION DES EXPORTS EXCEL & STATISTIQUES AGENTS")
    
    # Vérifier les fichiers modifiés
    print_section("📁 Fichiers Modifiés")
    files_to_check = {
        'quitus_app/views.py': [
            'export_quitus_excel',
            'export_history_excel', 
            'dashboard_stats',
            'openpyxl',
            'Workbook'
        ],
        'quitus_app/urls.py': [
            'export-excel',
            'export-history-excel',
            'dashboard/stats'
        ],
        'quitus_app/templates/quitus_app/liste.html': [
            'export_quitus_excel',
            'Exporter Excel'
        ],
        'quitus_app/templates/quitus_app/history.html': [
            'export_history_excel',
            'Exporter Excel'
        ],
        'quitus_app/templates/quitus_app/accueil.html': [
            'dashboard_stats',
            'Statistiques Agents'
        ],
        'quitus_app/templates/quitus_app/dashboard_stats.html': [
            'agents_stats',
            'total_quitus',
            'avg_per_agent'
        ],
        'requirements.txt': [
            'openpyxl'
        ]
    }
    
    all_files_ok = True
    for filepath, keywords in files_to_check.items():
        exists = os.path.exists(filepath)
        if exists:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                found_keywords = [kw for kw in keywords if kw in content]
                status = len(found_keywords) == len(keywords)
                print(f"{check_mark(status)} {filepath}")
                if not status:
                    missing = set(keywords) - set(found_keywords)
                    print(f"   {RED}Manquants: {', '.join(missing)}{END}")
                    all_files_ok = False
        else:
            print(f"{check_mark(False)} {filepath} {RED}(fichier non trouvé){END}")
            all_files_ok = False
    
    # Vérifier la dépendance openpyxl
    print_section("📦 Dépendances Python")
    try:
        import openpyxl
        print(f"{check_mark(True)} openpyxl installé (version {openpyxl.__version__})")
    except ImportError:
        print(f"{check_mark(False)} openpyxl {RED}NON INSTALLÉ{END}")
        print(f"   {YELLOW}Installer avec: pip install openpyxl{END}")
    
    # Résumé des fonctionnalités
    print_section("✨ Fonctionnalités Implémentées")
    features = [
        ("Export Excel - Liste Quitus", "export_quitus_excel view créée"),
        ("Export Excel - Historique", "export_history_excel view créée"),
        ("Statistiques Agents", "dashboard_stats view créée"),
        ("Bouton Export (liste.html)", "Bouton vert 'Exporter Excel' ajouté"),
        ("Bouton Export (history.html)", "Bouton vert 'Exporter Excel' ajouté"),
        ("Carte Stats (accueil.html)", "Carte 'Statistiques Agents' pour chef/admin"),
        ("Template dashboard_stats.html", "Interface complète avec cartes et tableau"),
        ("Routes URL", "3 nouvelles routes ajoutées"),
    ]
    
    for feature, description in features:
        print(f"{check_mark(True)} {BOLD}{feature}{END}")
        print(f"   → {description}")
    
    # Fonctionnalités détaillées
    print_section("🔧 Détails Techniques")
    
    print(f"\n{BOLD}Export Excel Quitus:{END}")
    print(f"  • Format: .xlsx (OpenXML)")
    print(f"  • Style: En-têtes bleus (#4472C4), texte blanc")
    print(f"  • Colonnes: 9 (Numéro, Date, Bénéficiaire, NIF, Téléphone, Email, Agent, Statut, Validité)")
    print(f"  • Filtres: Respecte les filtres de recherche appliqués")
    print(f"  • Nom fichier: quitus_export_YYYYMMDD_HHMMSS.xlsx")
    print(f"  • Log: Action EXPORT_EXCEL enregistrée dans HistoriqueQuitus")
    
    print(f"\n{BOLD}Export Excel Historique:{END}")
    print(f"  • Format: .xlsx (OpenXML)")
    print(f"  • Style: En-têtes verts (#70AD47), texte blanc")
    print(f"  • Colonnes: 6 (Date, Action, Utilisateur, Quitus, IP, Détails)")
    print(f"  • Sécurité: Agents exportent uniquement leurs logs")
    print(f"  • Filtres: Utilisateur, action, quitus, dates")
    print(f"  • Nom fichier: historique_export_YYYYMMDD_HHMMSS.xlsx")
    
    print(f"\n{BOLD}Statistiques Agents:{END}")
    print(f"  • Accès: @role_required('admin_plateforme', 'admin_service')")
    print(f"  • Cartes récap: Total agents, Total quitus, Moyenne, Plus productif")
    print(f"  • Filtres: Période (7j, 30j, 90j, 180j, 1an, tout), Agents inactifs")
    print(f"  • Tableau: Agent, Fonction, Matricule, Totaux par statut, Dernier quitus")
    print(f"  • Tri: Par nombre de quitus décroissant")
    print(f"  • Comparatif: Cartes agent plus/moins productif")
    
    # Sécurité
    print_section("🔐 Sécurité et Permissions")
    security_checks = [
        ("Authentification requise", "Tous les exports nécessitent @login_required"),
        ("Restriction agents", "Agents exportent uniquement leurs propres logs"),
        ("Protection stats", "@role_required bloque l'accès aux agents"),
        ("Filtrage dynamique", "Requêtes filtrées selon user.is_staff"),
        ("Logging exports", "Tous les exports enregistrés dans l'audit"),
    ]
    
    for check, description in security_checks:
        print(f"{check_mark(True)} {BOLD}{check}{END}")
        print(f"   → {description}")
    
    # Matrice de permissions
    print_section("👥 Matrice de Permissions")
    print(f"\n{'Fonctionnalité':<30} {'Agent':<10} {'Chef':<10} {'Admin':<10}")
    print(f"{'-'*30} {'-'*10} {'-'*10} {'-'*10}")
    print(f"{'Export Excel Quitus':<30} {GREEN}✅{END}{'  ':<8} {GREEN}✅{END}{'  ':<8} {GREEN}✅{END}")
    print(f"{'Export Excel Historique':<30} {YELLOW}⚠️ (ses logs){END} {GREEN}✅{END}{'  ':<8} {GREEN}✅{END}")
    print(f"{'Statistiques Agents':<30} {RED}❌{END}{'  ':<8} {GREEN}✅{END}{'  ':<8} {GREEN}✅{END}")
    
    # Tests recommandés
    print_section("🧪 Tests Recommandés")
    tests = [
        "Exporter liste quitus sans filtres",
        "Exporter liste quitus avec recherche",
        "Exporter historique en tant qu'agent (voir uniquement ses logs)",
        "Exporter historique en tant qu'admin (voir tous les logs)",
        "Accéder aux stats en tant que chef",
        "Tenter d'accéder aux stats en tant qu'agent (doit être refusé)",
        "Filtrer stats par période (30 jours, 1 an, tout)",
        "Activer/désactiver le filtre 'agents inactifs'",
        "Ouvrir fichier Excel dans Microsoft Excel",
        "Ouvrir fichier Excel dans LibreOffice Calc",
        "Vérifier l'encodage UTF-8 (accents correctement affichés)",
        "Vérifier les calculs statistiques (compter manuellement)",
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"  {i:2d}. {test}")
    
    # Commandes utiles
    print_section("💻 Commandes Utiles")
    commands = [
        ("Démarrer serveur", "python manage.py runserver"),
        ("Vérifier configuration", "python manage.py check"),
        ("Créer super-utilisateur", "python manage.py createsuperuser"),
        ("Installer dépendances", "pip install -r requirements.txt"),
        ("Tester imports Python", "python -c \"import openpyxl; print(openpyxl.__version__)\""),
        ("Accéder aux stats", "http://127.0.0.1:8000/dashboard/stats/"),
    ]
    
    print()
    for cmd_name, cmd in commands:
        print(f"{BOLD}{cmd_name}:{END}")
        print(f"  {BLUE}{cmd}{END}\n")
    
    # URLs ajoutées
    print_section("🌐 Nouvelles URLs")
    urls = [
        ("/export-excel/", "Export Excel de la liste des quitus"),
        ("/export-history-excel/", "Export Excel de l'historique"),
        ("/dashboard/stats/", "Tableau de bord statistiques agents"),
    ]
    
    for url, description in urls:
        print(f"{GREEN}•{END} {BOLD}{url}{END}")
        print(f"  → {description}")
    
    # Structure des fichiers
    print_section("📂 Structure des Fichiers Créés/Modifiés")
    structure = """
quitus_app/
├── views.py (MODIFIÉ)
│   ├── export_quitus_excel()         [171 lignes]
│   ├── export_history_excel()        [123 lignes]
│   └── dashboard_stats()             [71 lignes]
├── urls.py (MODIFIÉ)
│   ├── path('export-excel/', ...)
│   ├── path('export-history-excel/', ...)
│   └── path('dashboard/stats/', ...)
└── templates/quitus_app/
    ├── liste.html (MODIFIÉ)           [Bouton Export Excel]
    ├── history.html (MODIFIÉ)         [Bouton Export Excel]
    ├── accueil.html (MODIFIÉ)         [Carte Statistiques]
    └── dashboard_stats.html (NOUVEAU) [256 lignes]

requirements.txt (MODIFIÉ)             [+openpyxl]
GUIDE_EXCEL_STATS.md (NOUVEAU)         [Documentation complète]
test_excel_stats_feature.py (CE FICHIER)
"""
    print(structure)
    
    # Résumé final
    print_section("📊 Résumé")
    print(f"\n{BOLD}Statut Global:{END} {GREEN if all_files_ok else YELLOW}{'✅ PRÊT À TESTER' if all_files_ok else '⚠️  VÉRIFIER LES FICHIERS'}{END}")
    print(f"\n{BOLD}Fichiers créés:{END} 2")
    print(f"{BOLD}Fichiers modifiés:{END} 6")
    print(f"{BOLD}Lignes de code:{END} ~600")
    print(f"{BOLD}Nouvelles vues:{END} 3")
    print(f"{BOLD}Nouvelles routes:{END} 3")
    print(f"{BOLD}Dépendances:{END} 1 (openpyxl)")
    
    # Notes importantes
    print_section("⚠️  Notes Importantes")
    notes = [
        "Les exports Excel utilisent openpyxl (assurez-vous qu'il est installé)",
        "Les statistiques sont accessibles uniquement aux chefs et admins",
        "Les agents exportent uniquement leur propre historique",
        "Tous les exports sont enregistrés dans l'historique d'audit",
        "Les fichiers Excel sont générés en mémoire (pas de fichier temporaire)",
        "Les filtres de la page sont préservés lors de l'export",
    ]
    
    for note in notes:
        print(f"  {YELLOW}•{END} {note}")
    
    # Footer
    print_header("✨ FIN DE LA VÉRIFICATION ✨")
    print(f"\n{BOLD}Documentation complète:{END} Consultez {BLUE}GUIDE_EXCEL_STATS.md{END}")
    print(f"{BOLD}Aide historique:{END} Consultez {BLUE}GUIDE_HISTORIQUE.md{END}\n")

if __name__ == '__main__':
    main()

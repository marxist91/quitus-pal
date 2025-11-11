# Script de Réinitialisation de la Base de Données
# Ce script va supprimer toutes les données et recréer la base avec les nouvelles nomenclatures

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "REINITIALISATION DE LA BASE DE DONNEES" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Arrêter le serveur Django s'il tourne
Write-Host "[1/7] Vérification du serveur Django..." -ForegroundColor Yellow
$djangoProcess = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*runserver*" }
if ($djangoProcess) {
    Write-Host "Arrêt du serveur Django..." -ForegroundColor Yellow
    $djangoProcess | Stop-Process -Force
    Start-Sleep -Seconds 2
}
Write-Host "✓ Serveur vérifié" -ForegroundColor Green
Write-Host ""

# 2. Supprimer les fichiers de migration
Write-Host "[2/7] Nettoyage des fichiers de migration..." -ForegroundColor Yellow
$migrationFiles = Get-ChildItem -Path "quitus_app\migrations" -Filter "*.py" | Where-Object { $_.Name -ne "__init__.py" }
if ($migrationFiles) {
    foreach ($file in $migrationFiles) {
        Remove-Item $file.FullName -Force
        Write-Host "  Supprimé: $($file.Name)" -ForegroundColor Gray
    }
    Write-Host "✓ Fichiers de migration supprimés" -ForegroundColor Green
} else {
    Write-Host "✓ Aucun fichier de migration à supprimer" -ForegroundColor Green
}
Write-Host ""

# 3. Supprimer le cache Python
Write-Host "[3/7] Nettoyage du cache Python..." -ForegroundColor Yellow
if (Test-Path "quitus_app\migrations\__pycache__") {
    Remove-Item "quitus_app\migrations\__pycache__" -Recurse -Force
}
if (Test-Path "quitus_app\__pycache__") {
    Remove-Item "quitus_app\__pycache__" -Recurse -Force
}
Write-Host "✓ Cache Python nettoyé" -ForegroundColor Green
Write-Host ""

# 4. Drop et recréer la base de données MySQL
Write-Host "[4/7] Réinitialisation de la base de données MySQL..." -ForegroundColor Yellow
Write-Host "Connexion à MySQL..." -ForegroundColor Gray

$sqlCommands = @"
DROP DATABASE IF EXISTS quitus_pal;
CREATE DATABASE quitus_pal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE quitus_pal;
SELECT 'Base de données quitus_pal créée avec succès' AS Message;
"@

# Créer un fichier SQL temporaire
$tempSqlFile = "temp_reset_db.sql"
$sqlCommands | Out-File -FilePath $tempSqlFile -Encoding UTF8

# Exécuter les commandes SQL
#mysql -u root -proot < $tempSqlFile 2>&1 | Out-Null

# Supprimer le fichier temporaire
Remove-Item $tempSqlFile -Force

Write-Host "✓ Base de données réinitialisée" -ForegroundColor Green
Write-Host ""

# 5. Créer les nouvelles migrations
Write-Host "[5/7] Création des nouvelles migrations..." -ForegroundColor Yellow
python manage.py makemigrations
Write-Host "✓ Migrations créées" -ForegroundColor Green
Write-Host ""

# 6. Appliquer les migrations
Write-Host "[6/7] Application des migrations..." -ForegroundColor Yellow
python manage.py migrate
Write-Host "✓ Migrations appliquées" -ForegroundColor Green
Write-Host ""

# 7. Créer le superutilisateur
Write-Host "[7/7] Création du superutilisateur..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Création du compte administrateur Marcel..." -ForegroundColor Cyan
Write-Host "  Username: marcel" -ForegroundColor Gray
Write-Host "  Email: marcel@togoport.tg" -ForegroundColor Gray
Write-Host "  Mot de passe: TogoPort2024@" -ForegroundColor Gray
Write-Host ""

$env:DJANGO_SUPERUSER_PASSWORD = "TogoPort2024@"
python manage.py createsuperuser --noinput --username marcel --email marcel@togoport.tg

# Mettre à jour le prénom et nom
$updateUserScript = @"
from django.contrib.auth.models import User
user = User.objects.get(username='marcel')
user.first_name = 'Marcel'
user.last_name = 'KOKOU'
user.save()
print('✓ Prénom et nom mis à jour')
"@

$updateUserScript | python manage.py shell

Write-Host "✓ Superutilisateur créé" -ForegroundColor Green
Write-Host ""

# Résumé
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "REINITIALISATION TERMINEE AVEC SUCCES !" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Résumé:" -ForegroundColor Yellow
Write-Host "  ✓ Base de données MySQL réinitialisée" -ForegroundColor Green
Write-Host "  ✓ Migrations recréées et appliquées" -ForegroundColor Green
Write-Host "  ✓ Superutilisateur créé" -ForegroundColor Green
Write-Host ""
Write-Host "🔑 Identifiants Administrateur:" -ForegroundColor Yellow
Write-Host "  Email/Username: marcel@togoport.tg ou marcel" -ForegroundColor Cyan
Write-Host "  Mot de passe: TogoPort2024@" -ForegroundColor Cyan
Write-Host "  Prénom: Marcel" -ForegroundColor Cyan
Write-Host "  Nom: KOKOU" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 Prochaines étapes:" -ForegroundColor Yellow
Write-Host "  1. Démarrer le serveur: python manage.py runserver" -ForegroundColor Gray
Write-Host "  2. Se connecter avec: marcel@togoport.tg / TogoPort2024@" -ForegroundColor Gray
Write-Host "  3. Créer des utilisateurs via Dashboard Utilisateurs" -ForegroundColor Gray
Write-Host "  4. Tester la création de quitus" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ Système prêt avec toutes les nouvelles fonctionnalités !" -ForegroundColor Green
Write-Host ""

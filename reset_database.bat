@echo off
chcp 65001 >nul
color 0B
echo ========================================
echo RÉINITIALISATION DE LA BASE DE DONNÉES
echo ========================================
echo.

echo [ÉTAPE 1/7] Suppression des migrations...
del /F /Q quitus_app\migrations\0*.py 2>nul
echo ✓ Migrations supprimées
echo.

echo [ÉTAPE 2/7] Nettoyage du cache...
rmdir /S /Q quitus_app\migrations\__pycache__ 2>nul
rmdir /S /Q quitus_app\__pycache__ 2>nul
echo ✓ Cache nettoyé
echo.

echo [ÉTAPE 3/7] Suppression de l'ancienne base MySQL...
echo DROP DATABASE IF EXISTS quitus_pal; > temp_drop.sql
echo CREATE DATABASE quitus_pal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; >> temp_drop.sql
mysql -u root -proot < temp_drop.sql
del temp_drop.sql
echo ✓ Base de données réinitialisée
echo.

echo [ÉTAPE 4/7] Création des nouvelles migrations...
python manage.py makemigrations
echo.

echo [ÉTAPE 5/7] Application des migrations...
python manage.py migrate
echo.

echo [ÉTAPE 6/7] Création du superutilisateur...
set DJANGO_SUPERUSER_PASSWORD=TogoPort2024@
python manage.py createsuperuser --noinput --username marcel --email marcel@togoport.tg
echo.

echo [ÉTAPE 7/7] Configuration du profil utilisateur...
python -c "from django.contrib.auth.models import User; u = User.objects.get(username='marcel'); u.first_name = 'Marcel'; u.last_name = 'KOKOU'; u.save(); print('✓ Profil mis à jour')"
echo.

echo ========================================
echo ✅ RÉINITIALISATION TERMINÉE !
echo ========================================
echo.
echo 🔑 Identifiants:
echo    Email/Username: marcel@togoport.tg ou marcel
echo    Mot de passe: TogoPort2024@
echo    Nom complet: Marcel KOKOU
echo.
echo 🚀 Démarrer le serveur:
echo    python manage.py runserver
echo.
pause

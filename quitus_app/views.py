from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import FileResponse, HttpResponse, JsonResponse
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods
from .permissions import role_required, admin_required, agent_required, is_agent, is_admin_service
from io import BytesIO, StringIO
import csv
import qrcode
from datetime import datetime
from .forms import QuitusForm, SearchQuitusForm, LoginForm, UserRegistrationForm
from .models import Quitus, HistoriqueQuitus
from django.db.models import Q
from .pdf_generator import generate_quitus_pdf
from .audit import AuditLogger


def index(request):
    """Vue d'accueil - Page de base avec navigation"""
    from datetime import date, timedelta
    
    # Récupérer les statistiques
    today = date.today()
    quitus_all = Quitus.objects.all()
    
    stats = {
        'total': quitus_all.count(),
        'actif': quitus_all.filter(date_validite__gte=today).count(),
        'expire': quitus_all.filter(date_validite__lt=today).count(),
        'annule': quitus_all.filter(statut='ANNULE').count(),
    }
    
    return render(request, 'quitus_app/accueil.html', {'stats': stats})


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Vue de connexion utilisateur"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Enregistrer la connexion via AuditLogger
            AuditLogger.log_action(
                request,
                AuditLogger.ACTION_LOGIN,
                quitus=None,
                details=f"Connexion réussie: {user.username}"
            )
            
            messages.success(request, f"Bienvenue {user.first_name or user.username}!")
            
            # Redirection vers la page suivante ou l'accueil
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
        else:
            # Enregistrer la tentative de connexion échouée
            username = request.POST.get('username', 'inconnu')
            AuditLogger.log_failed_login(request, username)
    else:
        form = LoginForm()
    
    return render(request, 'quitus_app/login.html', {'form': form})


@login_required(login_url='login')
def logout_view(request):
    """Vue de déconnexion utilisateur"""
    username = request.user.username
    
    # Enregistrer la déconnexion via AuditLogger
    AuditLogger.log_action(
        request,
        AuditLogger.ACTION_LOGOUT,
        quitus=None,
        details=f"Déconnexion de: {username}"
    )
    
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('login')


def get_client_ip(request):
    """Récupérer l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generer_qr_code(data):
    """Générer un QR code"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer




@agent_required
def creer_quitus(request):
    """Vue pour créer un nouveau quitus"""
    if request.method == 'POST':
        form = QuitusForm(request.POST)
        if form.is_valid():
            # Créer le quitus
            quitus = form.save(commit=False)
            quitus.ip_creation = get_client_ip(request)
            
            # Générer le code de vérification avant la sauvegarde
            if not quitus.code_verification:
                quitus.code_verification = quitus.generer_code_verification()
            
            quitus.save()
            
            # Générer le QR code
            qr_data = f"https://www.togoport.tg/verifier/{quitus.code_verification}\n"
            qr_data += f"QUITUS: {quitus.numero_quitus}\n"
            qr_data += f"NOM: {quitus.nom_prenoms}\n"
            qr_data += f"VALIDE: {quitus.date_validite.strftime('%d/%m/%Y')}"
            
            qr_buffer = generer_qr_code(qr_data)
            quitus.qr_code = qr_data
            quitus.qr_code_image.save(
                f'qr_{quitus.numero_quitus}.png',
                ContentFile(qr_buffer.read()),
                save=False
            )
            
            # Générer le PDF
            pdf_buffer = generate_quitus_pdf(quitus)
            quitus.pdf_file.save(
                f'quitus_{quitus.numero_quitus}.pdf',
                ContentFile(pdf_buffer.read()),
                save=True
            )
            
            # Enregistrer la création via AuditLogger
            AuditLogger.log_action(
                request,
                AuditLogger.ACTION_CREATE_QUITUS,
                quitus=quitus,
                details=f"Quitus créé - Bénéficiaire: {quitus.nom_prenoms}, N°: {quitus.numero_quitus}"
            )
            
            messages.success(
                request, 
                f"Quitus {quitus.numero_quitus} généré avec succès ! "
                f"Code de vérification: {quitus.code_verification}"
            )
            
            # Rediriger vers la page de détail au lieu de télécharger directement
            return redirect('detail_quitus', numero_quitus=quitus.numero_quitus)
    else:
        form = QuitusForm()
    
    return render(request, 'quitus_app/form.html', {'form': form})


def telecharger_quitus(request, numero_quitus):
    """Télécharger un quitus existant"""
    try:
        quitus = Quitus.objects.get(numero_quitus=numero_quitus)
        
        # Enregistrer le téléchargement via AuditLogger
        AuditLogger.log_action(
            request,
            AuditLogger.ACTION_EXPORT_PDF,
            quitus=quitus,
            details=f"Téléchargement PDF - N°: {quitus.numero_quitus}"
        )
        
        if quitus.pdf_file:
            response = FileResponse(
                quitus.pdf_file.open('rb'),
                as_attachment=True,
                filename=f'quitus_{quitus.numero_quitus}.pdf'
            )
            # Ajouter message de succès dans la session pour affichage après redirection
            messages.success(request, f"Le quitus {quitus.numero_quitus} a été téléchargé avec succès.")
            return response
        else:
            # Régénérer le PDF si nécessaire
            pdf_buffer = generate_quitus_pdf(quitus)
            response = FileResponse(
                pdf_buffer,
                as_attachment=True,
                filename=f'quitus_{quitus.numero_quitus}.pdf'
            )
            messages.success(request, f"Le quitus {quitus.numero_quitus} a été téléchargé avec succès.")
            return response
    except Quitus.DoesNotExist:
        messages.error(request, "Quitus introuvable")
        return redirect('creer_quitus')


def verifier_quitus(request, code_verification):
    """Vérifier l'authenticité d'un quitus via QR code - Retourne JSON pour AJAX"""
    try:
        quitus = Quitus.objects.get(code_verification=code_verification)
        
        # Enregistrer la vérification via AuditLogger
        AuditLogger.log_action(
            request,
            AuditLogger.ACTION_VERIFICATION,
            quitus=quitus,
            details=f"Vérification QR code - N°: {quitus.numero_quitus}"
        )

        # Toujours retourner JSON si Accept header demande du JSON
        from datetime import date
        today = date.today()
        
        # Vérifier si c'est une requête AJAX/JSON
        accept_header = request.headers.get('Accept', '')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        is_json_accepted = 'application/json' in accept_header or 'text/plain' in accept_header
        
        if is_ajax or is_json_accepted or request.method == 'GET':
            # Retourner toujours JSON pour les requêtes GET (scanner QR)
            return JsonResponse({
                'valid': True,
                'numero_quitus': quitus.numero_quitus,
                'nom_prenoms': quitus.nom_prenoms,
                'raison_sociale': quitus.raison_sociale or '',
                'cni': quitus.cni,
                'date_emission': quitus.date_emission.strftime('%d/%m/%Y'),
                'date_validite': quitus.date_validite.strftime('%d/%m/%Y'),
                'statut': 'VALIDE' if quitus.date_validite >= today else 'EXPIRE',
                'agent': str(quitus.agent)
            }, content_type='application/json')
        
        context = {
            'quitus': quitus,
            'valide': quitus.est_valide,
            'jours_restants': quitus.jours_restants
        }
        # Utiliser le template placé dans templates/quitus_app/verification.html
        return render(request, 'quitus_app/verification.html', context)
    
    except Quitus.DoesNotExist:
        # Enregistrer une tentative de vérification échouée
        AuditLogger.log_suspicious_activity(
            request,
            'INVALID_VERIFICATION',
            f"Tentative de vérification avec code invalide: {code_verification}"
        )
        
        # Vérifier si c'est une requête AJAX/JSON
        accept_header = request.headers.get('Accept', '')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        is_json_accepted = 'application/json' in accept_header
        
        if is_ajax or is_json_accepted or request.method == 'GET':
            return JsonResponse({
                'valid': False,
                'message': 'Code de vérification invalide ou quitus inexistant'
            }, status=404, content_type='application/json')
        
        return render(request, 'quitus_app/verification.html', {
            'erreur': 'Code de vérification invalide ou quitus inexistant'
        })


def verification_page(request):
    """Page de vérification QR Code interactive"""
    return render(request, 'quitus_app/verification_qrcode.html')


def detail_quitus(request, numero_quitus):
    """Afficher le détail d'un quitus avec aperçu et lien de téléchargement"""
    try:
        quitus = Quitus.objects.select_related('agent').get(numero_quitus=numero_quitus)
        
        # Enregistrer la consultation via AuditLogger
        AuditLogger.log_action(
            request,
            AuditLogger.ACTION_VIEW_QUITUS,
            quitus=quitus,
            details=f"Consultation détail - N°: {quitus.numero_quitus}"
        )
        
        context = {
            'quitus': quitus,
            'valide': quitus.est_valide,
            'jours_restants': quitus.jours_restants,
            'historique': quitus.historique.all()[:10]  # Dernières 10 actions
        }
        return render(request, 'quitus_app/detail.html', context)
    
    except Quitus.DoesNotExist:
        messages.error(request, "Quitus introuvable")
        return redirect('creer_quitus')


@login_required(login_url='login')
def liste_quitus(request):
    """Lister tous les quitus avec pagination"""
    # Récupérer la liste triée
    quitus_all = Quitus.objects.select_related('agent').order_by('-date_emission')
    
    # Calculer les statistiques
    total = quitus_all.count()
    actif = quitus_all.filter(date_validite__gte=datetime.now().date()).count()
    expire = quitus_all.filter(date_validite__lt=datetime.now().date()).count()
    
    # Paginer (25 par page)
    paginator = Paginator(quitus_all, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'quitus_list': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'stats': {
            'total': total,
            'actif': actif,
            'expire': expire,
        }
    }
    return render(request, 'quitus_app/liste.html', context)


@login_required(login_url='login')
def recherche_quitus(request):
    """Recherche avancée de quitus via formulaire POST ou GET"""
    form = SearchQuitusForm(request.POST or request.GET)
    results = []
    query_used = False
    
    if request.POST or request.GET:
        if form.is_valid():
            query_used = True
            query = form.cleaned_data.get('query', '').strip()
            statut = form.cleaned_data.get('statut', '').strip()
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            
            # Commencer avec tous les quitus
            results = Quitus.objects.select_related('agent').all()
            
            # Filtrer par recherche textuelle
            if query:
                results = results.filter(
                    Q(numero_quitus__icontains=query) |
                    Q(nom_prenoms__icontains=query) |
                    Q(raison_sociale__icontains=query) |
                    Q(cni__icontains=query)
                )
            
            # Filtrer par statut
            if statut == 'VALIDE':
                results = results.filter(date_validite__gte=datetime.now().date())
            elif statut == 'EXPIRE':
                results = results.filter(date_validite__lt=datetime.now().date())
            elif statut == 'ANNULE':
                results = results.filter(statut='ANNULE')
            
            # Filtrer par plage de date de validité
            if date_from:
                results = results.filter(date_validite__gte=date_from)
            if date_to:
                results = results.filter(date_validite__lte=date_to)
            
            # Trier par date décroissante
            results = results.order_by('-date_emission')
    
    context = {
        'form': form,
        'results': results,
        'query_used': query_used,
        'result_count': len(results)
    }
    return render(request, 'quitus_app/recherche.html', context)


def verification(request, code_verification):
    """Page de vérification complète sans redirection"""
    try:
        quitus = Quitus.objects.select_related('agent').get(code_verification=code_verification)
        
        # Enregistrer la vérification
        HistoriqueQuitus.objects.create(
            quitus=quitus,
            action='VERIFICATION',
            ip_address=get_client_ip(request),
            details="Vérification via interface web"
        )
        
        context = {
            'quitus': quitus,
            'valide': quitus.est_valide,
            'jours_restants': quitus.jours_restants
        }
        return render(request, 'quitus_app/verification.html', context)
    
    except Quitus.DoesNotExist:
        return render(request, 'quitus_app/verification.html', {
            'erreur': 'Code de vérification invalide ou quitus inexistant'
        })


@login_required(login_url='login')
def export_quitus_csv(request):
    """Exporter la liste des quitus en fichier CSV"""
    # Récupérer les paramètres de filtrage depuis GET
    query = request.GET.get('q', '').strip()
    statut = request.GET.get('statut', '').strip()
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Commencer avec tous les quitus
    quitus_list = Quitus.objects.select_related('agent').all()
    
    # Appliquer les mêmes filtres que la recherche
    if query:
        quitus_list = quitus_list.filter(
            Q(numero_quitus__icontains=query) |
            Q(nom_prenoms__icontains=query) |
            Q(raison_sociale__icontains=query) |
            Q(cni__icontains=query)
        )
    
    if statut == 'VALIDE':
        quitus_list = quitus_list.filter(date_validite__gte=datetime.now().date())
    elif statut == 'EXPIRE':
        quitus_list = quitus_list.filter(date_validite__lt=datetime.now().date())
    elif statut == 'ANNULE':
        quitus_list = quitus_list.filter(statut='ANNULE')
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            quitus_list = quitus_list.filter(date_validite__gte=date_from_obj)
        except (ValueError, TypeError):
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            quitus_list = quitus_list.filter(date_validite__lte=date_to_obj)
        except (ValueError, TypeError):
            pass
    
    quitus_list = quitus_list.order_by('-date_emission')
    count = quitus_list.count()
    
    # Enregistrer l'export via AuditLogger
    AuditLogger.log_action(
        request,
        AuditLogger.ACTION_EXPORT_CSV,
        quitus=None,
        details=f"Export CSV de {count} quitus"
    )
    
    # Créer la réponse CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="quitus_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Ajouter BOM pour l'encodage UTF-8 (Excel)
    response.write('\ufeff')
    
    # Créer le writer CSV
    writer = csv.writer(response)
    
    # En-têtes
    writer.writerow([
        'Numéro Quitus',
        'Bénéficiaire',
        'Raison Sociale',
        'CNI',
        'Nationalité',
        'Activité',
        'N° Compte PAL',
        'N° NIF',
        'Téléphone',
        'Email',
        'Situation Géographique',
        'Adresse Postale',
        'Date Émission',
        'Date Validité',
        'Statut',
        'Agent Responsable'
    ])
    
    # Données
    for quitus in quitus_list:
        writer.writerow([
            quitus.numero_quitus,
            quitus.nom_prenoms,
            quitus.raison_sociale or '',
            quitus.cni,
            quitus.nationalite,
            quitus.activite,
            quitus.compte_pal,
            quitus.nif,
            quitus.telephone,
            quitus.email,
            quitus.situation_geo,
            quitus.adresse_postale,
            quitus.date_emission.strftime('%d/%m/%Y') if quitus.date_emission else '',
            quitus.date_validite.strftime('%d/%m/%Y') if quitus.date_validite else '',
            'Valide' if quitus.est_valide else ('Expiré' if quitus.date_validite < datetime.now().date() else 'Annulé'),
            quitus.agent.nom_complet if quitus.agent else ''
        ])
    
    return response


@role_required('admin_plateforme')
def manage_user_roles(request):
    """Vue pour gérer les rôles des utilisateurs (Admin uniquement)"""
    from .forms import UserRoleForm
    
    if request.method == 'POST':
        form = UserRoleForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Enregistrer le changement de rôle via AuditLogger
            AuditLogger.log_action(
                request,
                AuditLogger.ACTION_CHANGE_ROLE,
                quitus=None,
                details=f"Changement de rôle pour l'utilisateur: {user.username}"
            )
            
            messages.success(request, f"Rôle de {user.username} mis à jour avec succès!")
            return redirect('manage_user_roles')
    else:
        form = UserRoleForm()
    
    # Lister tous les utilisateurs avec leurs rôles
    users_with_roles = []
    for user in User.objects.filter(is_active=True):
        if user.is_superuser:
            role = 'Superuser'
        elif user.groups.exists():
            role = user.groups.first().name
        else:
            role = 'Sans rôle'
        users_with_roles.append({'user': user, 'role': role})
    
    context = {
        'form': form,
        'users_with_roles': users_with_roles,
    }
    return render(request, 'quitus_app/manage_roles.html', context)
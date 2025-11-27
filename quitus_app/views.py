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
from .forms import QuitusForm, SearchQuitusForm, LoginForm, UserRegistrationForm, AdminRenumberForm
from .models import Quitus, HistoriqueQuitus, HistoriqueNotifications, UserProfile, RenumberBatch
from django.db.models import Q, Count
from .pdf_generator import generate_quitus_pdf
from .audit import AuditLogger
from .notifications import NotificationManager
from django.views.decorators.http import require_GET
import re
import json
import uuid


def index(request):
    """Vue d'accueil - Page de base avec navigation"""
    from datetime import date, timedelta
    from dateutil.relativedelta import relativedelta
    
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


@login_required
@require_http_methods(["GET", "POST"])
def change_password(request):
    """Vue pour changer le mot de passe"""
    from .forms import PasswordChangeForm
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Important: Re-authentifier l'utilisateur après changement de mot de passe
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            
            # Enregistrer l'action
            AuditLogger.log_action(
                request,
                AuditLogger.ACTION_CUSTOM,
                quitus=None,
                details=f"Changement de mot de passe pour: {request.user.username}"
            )
            
            messages.success(request, "Votre mot de passe a été changé avec succès.")
            return redirect('index')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'quitus_app/change_password.html', {'form': form})


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


@login_required
def history_log(request):
    """Vue affichant l'historique global des actions (audit)"""
    from .models import HistoriqueQuitus
    
    qs = HistoriqueQuitus.objects.select_related('quitus').all()
    
    # Si l'utilisateur n'est ni admin ni chef, filtrer par ses propres actions
    if not (request.user.is_superuser or request.user.is_staff):
        qs = qs.filter(utilisateur=request.user.username)
    
    # Filtres
    user_q = request.GET.get('user', '').strip()
    action = request.GET.get('action', '').strip()
    numero = request.GET.get('numero', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    if user_q:
        qs = qs.filter(utilisateur__icontains=user_q)
    if action:
        qs = qs.filter(action__icontains=action)
    if numero:
        qs = qs.filter(quitus__numero_quitus__icontains=numero)
    if date_from:
        try:
            qs = qs.filter(date_action__date__gte=date_from)
        except Exception:
            pass
    if date_to:
        try:
            qs = qs.filter(date_action__date__lte=date_to)
        except Exception:
            pass
    
    # Pagination
    paginator = Paginator(qs, 25)
    page = request.GET.get('page')
    logs = paginator.get_page(page)
    
    # Actions distinctes pour le filtre (restreindre selon permissions)
    if request.user.is_superuser or request.user.is_staff:
        actions = HistoriqueQuitus.objects.values_list('action', flat=True).distinct()
    else:
        actions = HistoriqueQuitus.objects.filter(
            utilisateur=request.user.username
        ).values_list('action', flat=True).distinct()
    
    return render(request, 'quitus_app/history.html', {
        'logs': logs,
        'actions': actions,
        'filters': {
            'user': user_q,
            'action': action,
            'numero': numero,
            'date_from': date_from,
            'date_to': date_to,
        },
        'is_restricted': not (request.user.is_superuser or request.user.is_staff)
    })



@admin_required
@require_http_methods(["GET", "POST"])
def admin_regenerate_numeros(request):
    """Outil d'administration pour régénérer ou renommer des numéros de quitus.

    Sécurisé aux administrateurs de service (décorateur `admin_required`).
    - GET: affiche le formulaire
    - POST: effectue l'action choisie et affiche le résultat
    """
    form = AdminRenumberForm(request.POST or None)
    result = []

    # If this is a confirmation POST that only includes the batch_id (user clicked "Apply" on preview),
    # apply the persisted RenumberBatch without requiring the full form to be re-submitted.
    if request.method == 'POST' and request.POST.get('confirm') == '1' and request.POST.get('batch_id'):
        batch_id_post = request.POST.get('batch_id')
        batch = RenumberBatch.objects.filter(id=batch_id_post).first()
        if not batch:
            messages.error(request, "Batch introuvable pour application.")
            return render(request, 'quitus_app/admin_regen_numbers.html', {'form': form, 'result': result})

        # If already applied, nothing to do
        if batch.applied:
            messages.info(request, f"Le batch {batch.id} a déjà été appliqué.")
            return render(request, 'quitus_app/admin_regen_numbers.html', {'form': form, 'result': result})

        apply_changes = batch.changes or []
        changes_applied = []
        for entry in apply_changes:
            cid = entry.get('id')
            oldv = entry.get('old')
            newv = entry.get('new')
            q_obj = Quitus.objects.filter(id=cid).first()
            if not q_obj:
                continue
            q_obj.numero_quitus = newv
            q_obj.save()
            changes_applied.append((cid, oldv, newv))

            try:
                HistoriqueQuitus.objects.create(
                    quitus=q_obj,
                    action='MODIFICATION',
                    utilisateur=request.user.username if request.user.is_authenticated else 'system',
                    ip_address=get_client_ip(request),
                    details=json.dumps({'batch_id': str(batch.id), 'old': oldv, 'new': newv}, ensure_ascii=False)
                )
            except Exception:
                pass

        # Mark batch as applied and save results
        batch.applied = True
        batch.applied_by = request.user.username if request.user.is_authenticated else 'system'
        batch.applied_at = datetime.now()
        batch.result = [{'id': c[0], 'old': c[1], 'new': c[2]} for c in changes_applied]
        batch.save()

        for cid, oldv, newv in changes_applied:
            result.append({'id': cid, 'old': oldv, 'new': newv})

        if result:
            messages.success(request, f"{len(result)} quitus mis à jour.")
        else:
            messages.info(request, "Aucun changement effectué.")

        return render(request, 'quitus_app/admin_regen_numbers.html', {
            'form': form,
            'result': result
        })

    if request.method == 'POST' and form.is_valid():
        ids_raw = form.cleaned_data['quitus_ids']
        action = form.cleaned_data['action']
        new_prefix = form.cleaned_data.get('new_prefix') or ''
        start_number = form.cleaned_data.get('start_number')

        # Parse IDs (supporte virgules, espaces, nouvelles lignes) et nettoyer les espaces insécables
        raw_parts = [s.replace('\xa0', ' ') for s in re.split(r'[\n,;]+', ids_raw)]
        candidates = []
        for part in raw_parts:
            # split further on whitespace and commas
            for token in re.split(r'[\s,;]+', part):
                tok = token.strip()
                if tok:
                    # nettoyer NBSP et guillemets invisibles
                    tok = tok.replace('\u00A0', '').replace('\xa0', '')
                    candidates.append(tok)

        uuid_re = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
        uuid_ids = [c for c in candidates if uuid_re.match(c)]
        numero_ids = [c for c in candidates if not uuid_re.match(c)]

        # Construire queryset en acceptant soit des UUID (id) soit des numero_quitus
        q_filter = Q()
        if uuid_ids:
            q_filter |= Q(id__in=uuid_ids)
        if numero_ids:
            # normaliser les numéros (suppression espaces & majuscules)
            numero_norm = [n.strip().upper() for n in numero_ids]
            q_filter |= Q(numero_quitus__in=numero_norm)

        qs = Quitus.objects.filter(q_filter) if q_filter else Quitus.objects.none()

        if not qs.exists():
            messages.error(request, "Aucun quitus trouvé pour les IDs fournis.")
            return render(request, 'quitus_app/admin_regen_numbers.html', {'form': form, 'result': result})

        # --- Construire la liste de changements proposés (preview) sans appliquer ---
        proposed_changes = []

        if action == 'regenerate':
            # Group by year and compute next available numbers excluding selected
            by_year = {}
            for q in qs:
                year = q.date_creation.year if getattr(q, 'date_creation', None) else datetime.now().year
                by_year.setdefault(year, []).append(q)

            for year, items in by_year.items():
                prefix_year = f"PAL-{year}-"
                selected_ids = list(qs.values_list('id', flat=True))
                # Compute the current max suffix across ALL quitus for this prefix
                all_with_prefix = Quitus.objects.filter(numero_quitus__startswith=prefix_year)
                max_num = 0
                for o in all_with_prefix:
                    try:
                        suffix = o.numero_quitus.split('-')[-1]
                        n = int(suffix)
                        if n > max_num:
                            max_num = n
                    except Exception:
                        continue

                next_num = max_num + 1
                for item in sorted(items, key=lambda x: getattr(x, 'date_creation', datetime.now())):
                    new_num = f"{prefix_year}{next_num:03d}"
                    # avoid collisions
                    while Quitus.objects.filter(numero_quitus=new_num).exclude(id=item.id).exists():
                        next_num += 1
                        new_num = f"{prefix_year}{next_num:03d}"
                    proposed_changes.append({'id': str(item.id), 'old': item.numero_quitus, 'new': new_num})
                    next_num += 1

        elif action == 'rename_prefix':
            prefix = new_prefix.strip()
            if not prefix:
                messages.error(request, "Le nouveau préfixe est requis pour l'action de renommage.")
                return render(request, 'quitus_app/admin_regen_numbers.html', {'form': form, 'result': result})
            if not prefix.endswith('-'):
                prefix = prefix + '-'

            if start_number:
                next_num = int(start_number)
            else:
                selected_ids = list(qs.values_list('id', flat=True))
                # Compute max across all quitus that already use this prefix so new numbers follow the current max
                all_with_prefix = Quitus.objects.filter(numero_quitus__startswith=prefix)
                max_num = 0
                for o in all_with_prefix:
                    try:
                        suffix = o.numero_quitus.split('-')[-1]
                        n = int(suffix)
                        if n > max_num:
                            max_num = n
                    except Exception:
                        continue
                next_num = max_num + 1

            for item in sorted(qs, key=lambda x: getattr(x, 'date_creation', datetime.now())):
                new_num = f"{prefix}{next_num:03d}"
                while Quitus.objects.filter(numero_quitus=new_num).exclude(id=item.id).exists():
                    next_num += 1
                    new_num = f"{prefix}{next_num:03d}"
                proposed_changes.append({'id': str(item.id), 'old': item.numero_quitus, 'new': new_num})
                next_num += 1

        # If the user didn't confirm yet, show preview page and store proposal in session
        confirmed = request.POST.get('confirm') == '1'
        batch_id = str(uuid.uuid4())
        if not confirmed:
            # Persist preview in DB for multi-user auditing and later export/undo
            batch = RenumberBatch.objects.create(
                action=action,
                params={'new_prefix': new_prefix, 'start_number': start_number},
                changes=proposed_changes,
                created_by=request.user.username if request.user.is_authenticated else 'system',
            )
            return render(request, 'quitus_app/admin_regen_preview.html', {
                'form': form,
                'preview': batch,
            })

        # Confirmed -> apply changes stored in session if available
        # Load persisted batch if provided
        batch_id_post = request.POST.get('batch_id')
        apply_changes = proposed_changes
        batch = None
        if batch_id_post:
            try:
                batch = RenumberBatch.objects.filter(id=batch_id_post).first()
                if batch and batch.changes:
                    apply_changes = batch.changes
            except Exception:
                batch = None
        if batch:
            batch.applied = True
            batch.applied_by = request.user.username if request.user.is_authenticated else 'system'
            batch.applied_at = datetime.now()
            # we'll fill result after applying
            batch.save()

        changes_applied = []
        for entry in apply_changes:
            cid = entry['id']
            oldv = entry['old']
            newv = entry['new']
            q_obj = Quitus.objects.filter(id=cid).first()
            if not q_obj:
                continue
            q_obj.numero_quitus = newv
            q_obj.save()
            changes_applied.append((cid, oldv, newv))

            # enregistrer l'historique détaillé (JSON dans details)
            try:
                HistoriqueQuitus.objects.create(
                    quitus=q_obj,
                    action='MODIFICATION',
                    utilisateur=request.user.username if request.user.is_authenticated else 'system',
                    ip_address=get_client_ip(request),
                    details=json.dumps({'batch_id': batch_id, 'old': oldv, 'new': newv}, ensure_ascii=False)
                )
            except Exception:
                pass

        # Save result into batch if present
        if batch:
            batch.result = result
            batch.save()

        # Build result for display
        for cid, oldv, newv in changes_applied:
            result.append({'id': cid, 'old': oldv, 'new': newv})

        if result:
            messages.success(request, f"{len(result)} quitus mis à jour.")
        else:
            messages.info(request, "Aucun changement effectué.")

    return render(request, 'quitus_app/admin_regen_numbers.html', {
        'form': form,
        'result': result
    })


@admin_required
@require_GET
def admin_regenerate_export_csv(request):
    """Exporter la preview ou le dernier résultat stocké en session en CSV."""
    preview = request.session.get('admin_renumber_preview')
    result = request.session.get('admin_renumber_result')

    rows = []
    if preview:
        rows = preview.get('changes', [])
        batch = preview.get('batch_id')
    elif result:
        rows = result
        batch = None
    else:
        messages.error(request, "Aucune donnée à exporter.")
        return redirect('admin_regenerate_numeros')

    import csv
    from django.utils.encoding import smart_str
    response = HttpResponse(content_type='text/csv')
    fname = f"renumber_changes_{batch or 'result'}.csv"
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    writer = csv.writer(response)
    writer.writerow(['id', 'old', 'new'])
    for r in rows:
        writer.writerow([smart_str(r.get('id')), smart_str(r.get('old')), smart_str(r.get('new'))])
    return response


@admin_required
@require_http_methods(["POST"])
def admin_regenerate_undo(request, batch_id):
    """Annuler une opération précédente identifiée par `batch_id`.

    Cette vue recherche dans `HistoriqueQuitus.details` les enregistrements JSON contenant le batch_id
    et restaure les anciens numéros. Elle crée aussi des entrées d'historique pour l'annulation.
    """
    # Rechercher les historiques correspondants
    entries = HistoriqueQuitus.objects.filter(details__contains=batch_id)
    if not entries.exists():
        messages.error(request, "Aucun historique trouvé pour ce batch_id.")
        return redirect('admin_regenerate_numeros')

    changes_done = []
    for e in entries:
        try:
            payload = json.loads(e.details)
            old = payload.get('old')
            new = payload.get('new')
            q = e.quitus
            if q and q.numero_quitus == new:
                q.numero_quitus = old
                q.save()
                changes_done.append((str(q.id), new, old))
                # journaliser l'annulation
                HistoriqueQuitus.objects.create(
                    quitus=q,
                    action='MODIFICATION',
                    utilisateur=request.user.username if request.user.is_authenticated else 'system',
                    ip_address=get_client_ip(request),
                    details=json.dumps({'batch_id': batch_id, 'undo': True, 'restored_from': new, 'restored_to': old}, ensure_ascii=False)
                )
        except Exception:
            continue

    if changes_done:
        messages.success(request, f"{len(changes_done)} quitus restaurés depuis le batch {batch_id}.")
    else:
        messages.info(request, "Aucun changement effectué lors de l'annulation.")

    return redirect('admin_regenerate_numeros')


@admin_required
@require_GET
def admin_list_batches(request):
    """Lister tous les RenumberBatch pour supervision."""
    batches = RenumberBatch.objects.all().order_by('-created_at')
    return render(request, 'quitus_app/admin_renumber_batches.html', {
        'batches': batches
    })


@admin_required
@require_GET
def admin_preview_batch(request, batch_id):
    """Afficher une prévisualisation persistée pour un batch donné."""
    batch = RenumberBatch.objects.filter(id=batch_id).first()
    if not batch:
        messages.error(request, "Batch introuvable.")
        return redirect('admin_regenerate_numeros')
    return render(request, 'quitus_app/admin_regen_preview.html', {
        'form': AdminRenumberForm(),
        'preview': batch,
    })




@agent_required
def creer_quitus(request):
    """Vue pour créer un nouveau quitus"""
    # Calculer numéro automatique (PAL-<année>-<num>)
    from datetime import date
    current_year = date.today().year
    prefix = f"PAL-{current_year}-"

    def _next_numero():
        qs = Quitus.objects.filter(numero_quitus__startswith=prefix)
        max_num = 0
        for q in qs:
            try:
                suffix = q.numero_quitus.split('-')[-1]
                n = int(suffix)
                if n > max_num:
                    max_num = n
            except Exception:
                continue
        return f"{prefix}{(max_num + 1):03d}"

    default_numero = _next_numero()
    default_date_validite = date(current_year, 12, 31)

    if request.method == 'POST':
        # Uppercase compte_pal for consistent format
        post = request.POST.copy()
        if 'compte_pal' in post:
            post['compte_pal'] = post['compte_pal'].strip().upper()

        # If date_validite is not provided in the POST, set it to the default (31/12/current_year)
        if not post.get('date_validite'):
            try:
                post['date_validite'] = default_date_validite.isoformat()
            except Exception:
                pass

        form = QuitusForm(post)
        # Validate compte_pal server-side
        compte = post.get('compte_pal', '').strip().upper()
        if compte and not re.match(r'^C\d{6}$', compte):
            form.add_error('compte_pal', 'Format du compte PAL invalide (ex: C123456).')
        
        if form.is_valid():
            # Créer le quitus
            quitus = form.save(commit=False)
            quitus.ip_creation = get_client_ip(request)
            
            # Associer l'utilisateur connecté comme créateur
            if request.user.is_authenticated:
                quitus.created_by = request.user
            
            # Générer le code de vérification avant la sauvegarde
            if not quitus.code_verification:
                quitus.code_verification = quitus.generer_code_verification()
            
            # Si numero_quitus vide ou laissé par l'utilisateur, générer
            if not quitus.numero_quitus:
                quitus.numero_quitus = default_numero
            # Si date_validite non fournie, définir au 31/12 de l'année en cours
            if not quitus.date_validite:
                quitus.date_validite = default_date_validite

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
            # Afficher les erreurs de validation
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Pré-remplir numero et date_validite
        form = QuitusForm(initial={
            'numero_quitus': default_numero,
            'date_validite': default_date_validite,
        })
    
    # L'utilisateur connecté sera automatiquement utilisé comme créateur
    user_has_agent = request.user.is_authenticated
    
    return render(request, 'quitus_app/form.html', {
        'form': form,
        'user_has_agent': user_has_agent,
        'default_date_validite': default_date_validite,
    })


@require_GET
def client_by_compte(request):
    """Endpoint AJAX: retourne les infos client à partir du compte PAL (si trouvé)
    Recherche la dernière entrée Quitus correspondant au `compte_pal` fourni.
    """
    compte = request.GET.get('compte', '').strip().upper()
    if not compte:
        return JsonResponse({'found': False})

    # Chercher dans quitus existants
    q = Quitus.objects.filter(compte_pal__iexact=compte).order_by('-date_creation').first()
    if not q:
        return JsonResponse({'found': False})

    data = {
        'found': True,
        'nom_prenoms': q.nom_prenoms,
        'raison_sociale': q.raison_sociale,
        'cni': q.cni,
        'nif': q.nif,
        'telephone': q.telephone,
        'email': q.email,
        'situation_geo': q.situation_geo,
        'adresse_postale': q.adresse_postale,
    }
    return JsonResponse(data)


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
    """Vérifier l'authenticité d'un quitus via code de vérification"""
    try:
        quitus = Quitus.objects.get(code_verification=code_verification)
        
        # Enregistrer la vérification via AuditLogger
        AuditLogger.log_action(
            request,
            AuditLogger.ACTION_VERIFICATION,
            quitus=quitus,
            details=f"Vérification QR code - N°: {quitus.numero_quitus}"
        )

        from datetime import date
        today = date.today()
        
        # Vérifier si c'est une requête AJAX/JSON explicite
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        accept_header = request.headers.get('Accept', '')
        wants_json = 'application/json' in accept_header and 'text/html' not in accept_header
        
        # Retourner JSON uniquement si explicitement demandé (API, AJAX)
        if is_ajax or wants_json:
            return JsonResponse({
                'valid': True,
                'numero_quitus': quitus.numero_quitus,
                'nom_prenoms': quitus.nom_prenoms,
                'raison_sociale': quitus.raison_sociale or '',
                'cni': quitus.cni,
                'date_emission': quitus.date_emission.strftime('%d/%m/%Y'),
                'date_validite': quitus.date_validite.strftime('%d/%m/%Y'),
                'statut': 'VALIDE' if quitus.date_validite >= today else 'EXPIRE',
                'created_by': quitus.created_by.get_full_name() if quitus.created_by else ''
            }, content_type='application/json')
        
        # Par défaut, afficher la page HTML
        context = {
            'quitus': quitus,
            'valide': quitus.est_valide,
            'jours_restants': quitus.jours_restants
        }
        return render(request, 'quitus_app/verification.html', context)
    
    except Quitus.DoesNotExist:
        # Enregistrer une tentative de vérification échouée
        AuditLogger.log_suspicious_activity(
            request,
            'INVALID_VERIFICATION',
            f"Tentative de vérification avec code invalide: {code_verification}"
        )
        
        # Vérifier si c'est une requête AJAX/JSON
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        accept_header = request.headers.get('Accept', '')
        wants_json = 'application/json' in accept_header and 'text/html' not in accept_header
        
        if is_ajax or wants_json:
            return JsonResponse({
                'valid': False,
                'message': 'Code de vérification invalide ou quitus inexistant'
            }, status=404, content_type='application/json')
        
        return render(request, 'quitus_app/verification.html', {
            'erreur': 'Code de vérification invalide ou quitus inexistant'
        })


@login_required(login_url='login')
def verification_page(request):
    """Page de vérification QR Code interactive"""
    return render(request, 'quitus_app/verification_qrcode.html')


def detail_quitus(request, numero_quitus):
    """Afficher le détail d'un quitus avec aperçu et lien de téléchargement"""
    try:
        quitus = Quitus.objects.select_related('created_by').get(numero_quitus=numero_quitus)
        
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
    quitus_all = Quitus.objects.select_related('created_by').order_by('-date_emission')
    
    # Filtrer par utilisateur si c'est un agent (pas chef/admin)
    if not (request.user.is_staff or request.user.is_superuser):
        # Les agents voient uniquement leurs propres quitus
        quitus_all = quitus_all.filter(created_by=request.user)
    
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
            results = Quitus.objects.select_related('created_by').all()
            
            # Filtrer par utilisateur si c'est un agent (pas chef/admin)
            if not (request.user.is_staff or request.user.is_superuser):
                # Les agents voient uniquement leurs propres quitus
                results = results.filter(created_by=request.user)
            
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


@login_required(login_url='login')
def verification(request, code_verification):
    """Page de vérification complète sans redirection"""
    try:
        quitus = Quitus.objects.select_related('created_by').get(code_verification=code_verification)
        
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
    quitus_list = Quitus.objects.select_related('created_by').all()
    
    # Filtrer par utilisateur si c'est un agent (pas chef/admin)
    if not (request.user.is_staff or request.user.is_superuser):
        # Les agents voient uniquement leurs propres quitus
        quitus_list = quitus_list.filter(created_by=request.user)
    
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
            quitus.created_by.get_full_name() if quitus.created_by else ''
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


# ============================================================================
# GESTION DES UTILISATEURS - DASHBOARD
# ============================================================================

@login_required(login_url='login')
def dashboard_users(request):
    """Dashboard de gestion des utilisateurs - Accessible aux admins et chefs"""
    # Vérifier les permissions
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Vous n'avez pas l'autorisation d'accéder à cette page.")
        return redirect('index')
    
    # Récupérer tous les utilisateurs avec leurs statistiques
    users = User.objects.all().order_by('-date_joined')
    
    users_data = []
    for user in users:
        # Déterminer le rôle
        if user.is_superuser:
            role = 'admin'
            role_display = 'Admin Plateforme'
            role_badge = 'danger'
        elif user.is_staff:
            role = 'chef'
            role_display = 'Chef de Service'
            role_badge = 'warning'
        else:
            role = 'agent'
            role_display = 'Agent'
            role_badge = 'info'
        
        # Compter les quitus créés par cet utilisateur
        quitus_count = Quitus.objects.filter(created_by=user).count()
        
        users_data.append({
            'user': user,
            'role': role,
            'role_display': role_display,
            'role_badge': role_badge,
            'quitus_count': quitus_count,
        })
    
    # Statistiques
    stats = {
        'total': users.count(),
        'actifs': users.filter(is_active=True).count(),
        'inactifs': users.filter(is_active=False).count(),
        'admins': users.filter(is_superuser=True).count(),
        'chefs': users.filter(is_staff=True, is_superuser=False).count(),
        'agents': users.filter(is_staff=False).count(),
    }
    
    context = {
        'users_data': users_data,
        'stats': stats,
    }
    
    return render(request, 'quitus_app/dashboard_users.html', context)


@login_required(login_url='login')
def add_user(request):
    """Ajouter un nouvel utilisateur - Accessible aux admins et chefs"""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Vous n'avez pas l'autorisation d'accéder à cette page.")
        return redirect('index')
    
    from .forms import UserRoleForm
    
    if request.method == 'POST':
        form = UserRoleForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Enregistrer l'ajout via AuditLogger
            AuditLogger.log_action(
                request,
                AuditLogger.ACTION_CREATE_USER if hasattr(AuditLogger, 'ACTION_CREATE_USER') else 'CREATE_USER',
                quitus=None,
                details=f"Nouvel utilisateur créé: {user.username} ({user.get_full_name()}) - Rôle: {form.cleaned_data['role']}"
            )
            
            messages.success(
                request, 
                f"✅ Utilisateur {user.username} créé avec succès ! "
                f"Rôle: {dict(form.ROLE_CHOICES)[form.cleaned_data['role']]}"
            )
            return redirect('dashboard_users')
    else:
        form = UserRoleForm()
    
    context = {
        'form': form,
        'page_title': 'Ajouter un utilisateur',
    }
    
    return render(request, 'quitus_app/user_form.html', context)


@login_required(login_url='login')
def edit_user(request, user_id):
    """Modifier un utilisateur existant - Accessible aux admins et chefs"""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Vous n'avez pas l'autorisation d'accéder à cette page.")
        return redirect('index')
    
    from .forms import UserEditForm
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Utilisateur introuvable.")
        return redirect('dashboard_users')
    
    # Empêcher la modification de son propre compte par cette interface
    if user == request.user:
        messages.warning(request, "Vous ne pouvez pas modifier votre propre compte via cette interface.")
        return redirect('dashboard_users')
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            updated_user = form.save()
            
            # Enregistrer la modification via AuditLogger
            AuditLogger.log_action(
                request,
                AuditLogger.ACTION_MODIFY_USER if hasattr(AuditLogger, 'ACTION_MODIFY_USER') else 'MODIFY_USER',
                quitus=None,
                details=f"Utilisateur modifié: {updated_user.username} - Rôle: {form.cleaned_data['role']}"
            )
            
            messages.success(request, f"✅ Utilisateur {updated_user.username} modifié avec succès !")
            return redirect('dashboard_users')
    else:
        form = UserEditForm(instance=user)
    
    context = {
        'form': form,
        'user_to_edit': user,
        'page_title': f'Modifier {user.username}',
    }
    
    return render(request, 'quitus_app/user_form.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def delete_user(request, user_id):
    """Supprimer un utilisateur - Accessible uniquement aux admins"""
    if not request.user.is_superuser:
        messages.error(request, "Seuls les administrateurs peuvent supprimer des utilisateurs.")
        return redirect('dashboard_users')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Utilisateur introuvable.")
        return redirect('dashboard_users')
    
    # Empêcher la suppression de son propre compte
    if user == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte !")
        return redirect('dashboard_users')
    
    username = user.username
    user.delete()
    
    # Enregistrer la suppression via AuditLogger
    AuditLogger.log_action(
        request,
        AuditLogger.ACTION_DELETE_USER if hasattr(AuditLogger, 'ACTION_DELETE_USER') else 'DELETE_USER',
        quitus=None,
        details=f"Utilisateur supprimé: {username}"
    )
    
    messages.success(request, f"🗑️ Utilisateur {username} supprimé avec succès.")
    return redirect('dashboard_users')


@login_required(login_url='login')
@require_http_methods(["POST"])
def toggle_user_status(request, user_id):
    """Activer/Désactiver un utilisateur - Accessible aux admins et chefs"""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Vous n'avez pas l'autorisation d'effectuer cette action.")
        return redirect('dashboard_users')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Utilisateur introuvable.")
        return redirect('dashboard_users')
    
    # Empêcher la désactivation de son propre compte
    if user == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte !")
        return redirect('dashboard_users')
    
    # Inverser le statut
    user.is_active = not user.is_active
    user.save()
    
    status = "activé" if user.is_active else "désactivé"
    
    # Enregistrer le changement via AuditLogger
    AuditLogger.log_action(
        request,
        AuditLogger.ACTION_TOGGLE_USER if hasattr(AuditLogger, 'ACTION_TOGGLE_USER') else 'TOGGLE_USER_STATUS',
        quitus=None,
        details=f"Utilisateur {status}: {user.username}"
    )
    
    messages.success(request, f"✅ Utilisateur {user.username} {status} avec succès.")
    return redirect('dashboard_users')


@login_required(login_url='login')
def export_quitus_excel(request):
    """
    Exporter la liste des quitus en format Excel (.xlsx)
    Accessible à tous les utilisateurs authentifiés
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from datetime import datetime
    
    # Récupérer les quitus (avec même logique que liste_quitus)
    quitus_list = Quitus.objects.select_related('created_by').all().order_by('-date_creation')
    
    # Filtrer par utilisateur si c'est un agent (pas chef/admin)
    if not (request.user.is_staff or request.user.is_superuser):
        # Les agents voient uniquement leurs propres quitus
        quitus_list = quitus_list.filter(created_by=request.user)
    
    # Appliquer les filtres si présents
    search_query = request.GET.get('search', '').strip()
    if search_query:
        quitus_list = quitus_list.filter(
            Q(numero_quitus__icontains=search_query) |
            Q(beneficiaire__icontains=search_query) |
            Q(nif_beneficiaire__icontains=search_query)
        )
    
    # Créer le workbook Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Liste des Quitus"
    
    # En-têtes
    headers = [
        'Numéro Quitus',
        'Date Création',
        'Bénéficiaire',
        'NIF',
        'Téléphone',
        'Email',
        'Agent',
        'Statut',
        'Date de Validité'
    ]
    
    # Style pour les en-têtes
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Écrire les en-têtes
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    # Écrire les données
    for row_num, quitus in enumerate(quitus_list, 2):
        ws.cell(row=row_num, column=1, value=quitus.numero_quitus)
        ws.cell(row=row_num, column=2, value=quitus.date_creation.strftime('%d/%m/%Y %H:%M') if quitus.date_creation else '')
        ws.cell(row=row_num, column=3, value=quitus.beneficiaire)
        ws.cell(row=row_num, column=4, value=quitus.nif_beneficiaire)
        ws.cell(row=row_num, column=5, value=quitus.telephone_beneficiaire or '')
        ws.cell(row=row_num, column=6, value=quitus.email_beneficiaire or '')
        ws.cell(row=row_num, column=7, value=quitus.created_by.get_full_name() if quitus.created_by else '')
        ws.cell(row=row_num, column=8, value=quitus.statut)
        ws.cell(row=row_num, column=9, value=quitus.date_validite.strftime('%d/%m/%Y') if quitus.date_validite else '')
    
    # Ajuster la largeur des colonnes
    column_widths = [20, 18, 30, 15, 15, 30, 25, 12, 15]
    for col_num, width in enumerate(column_widths, 1):
        ws.column_dimensions[chr(64 + col_num)].width = width
    
    # Préparer la réponse HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"quitus_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Sauvegarder le workbook dans la réponse
    wb.save(response)
    
    # Enregistrer l'export dans l'historique
    AuditLogger.log_action(
        request,
        'EXPORT_EXCEL',
        quitus=None,
        details=f"Export Excel de {quitus_list.count()} quitus"
    )
    
    return response


@login_required(login_url='login')
def export_history_excel(request):
    """
    Exporter l'historique des actions en format Excel (.xlsx)
    Respecte les filtres de rôle (agents voient uniquement leurs logs)
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from datetime import datetime
    
    # Récupérer les logs avec même logique que history_log
    logs = HistoriqueQuitus.objects.all().order_by('-date_action')
    
    # Restriction par rôle
    if not (request.user.is_staff or request.user.is_superuser):
        logs = logs.filter(utilisateur=request.user.username)
    
    # Appliquer les filtres
    user_filter = request.GET.get('user', '').strip()
    action_filter = request.GET.get('action', '').strip()
    quitus_filter = request.GET.get('quitus', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    if user_filter and (request.user.is_staff or request.user.is_superuser):
        logs = logs.filter(utilisateur__icontains=user_filter)
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if quitus_filter:
        logs = logs.filter(quitus__numero_quitus__icontains=quitus_filter)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(date_action__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            from datetime import timedelta
            logs = logs.filter(date_action__lte=date_to_obj + timedelta(days=1))
        except ValueError:
            pass
    
    # Créer le workbook Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Historique des Actions"
    
    # En-têtes
    headers = [
        'Date & Heure',
        'Action',
        'Utilisateur',
        'Quitus',
        'Adresse IP',
        'Détails'
    ]
    
    # Style pour les en-têtes
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Écrire les en-têtes
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    # Écrire les données
    for row_num, log in enumerate(logs, 2):
        ws.cell(row=row_num, column=1, value=log.date_action.strftime('%d/%m/%Y %H:%M:%S') if log.date_action else '')
        ws.cell(row=row_num, column=2, value=log.action)
        ws.cell(row=row_num, column=3, value=log.utilisateur)
        ws.cell(row=row_num, column=4, value=log.quitus.numero_quitus if log.quitus else '')
        ws.cell(row=row_num, column=5, value=log.ip_address or '')
        ws.cell(row=row_num, column=6, value=log.details or '')
    
    # Ajuster la largeur des colonnes
    column_widths = [20, 20, 20, 20, 15, 50]
    for col_num, width in enumerate(column_widths, 1):
        ws.column_dimensions[chr(64 + col_num)].width = width
    
    # Préparer la réponse HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"historique_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Sauvegarder le workbook dans la réponse
    wb.save(response)
    
    # Enregistrer l'export dans l'historique
    AuditLogger.log_action(
        request,
        'EXPORT_EXCEL',
        quitus=None,
        details=f"Export Excel de {logs.count()} entrées d'historique"
    )
    
    return response


@login_required(login_url='login')
@role_required('admin_plateforme', 'admin_service')
def dashboard_stats(request):
    """
    Tableau de bord des statistiques par agent
    Accessible uniquement aux chefs et admins
    """
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    # Filtre de période
    period = request.GET.get('period', '30')  # Par défaut 30 jours
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    if days > 0:
        date_from = datetime.now() - timedelta(days=days)
        quitus_filter = Q(quitus_crees__date_creation__gte=date_from)
    else:
        quitus_filter = Q()  # Tous les quitus
    
    # Statistiques par créateur (utilisateur)
    from django.contrib.auth.models import User
    users_stats = User.objects.select_related('profile').annotate(
        total_quitus=Count('quitus_crees', filter=quitus_filter),
        actifs=Count('quitus_crees', filter=quitus_filter & Q(quitus_crees__statut='ACTIF')),
        expires=Count('quitus_crees', filter=quitus_filter & Q(quitus_crees__statut='EXPIRÉ')),
        annules=Count('quitus_crees', filter=quitus_filter & Q(quitus_crees__statut='ANNULÉ'))
    ).filter(total_quitus__gt=0).order_by('-total_quitus')
    
    # Filtrer uniquement les utilisateurs actifs ou tous
    show_inactive = request.GET.get('show_inactive', '') == 'true'
    if not show_inactive:
        users_stats = users_stats.filter(is_active=True)
    
    # Statistiques globales
    total_users = users_stats.count()
    total_quitus = sum(user.total_quitus for user in users_stats)
    avg_per_user = total_quitus / total_users if total_users > 0 else 0
    
    most_productive = users_stats.first() if users_stats.exists() else None
    least_productive = users_stats.filter(total_quitus__gt=0).last() if users_stats.exists() else None
    
    # Récupérer le dernier quitus pour chaque utilisateur
    for user in users_stats:
        last_quitus = Quitus.objects.filter(created_by=user).order_by('-date_creation').first()
        user.last_quitus_date = last_quitus.date_creation if last_quitus else None
    
    context = {
        'agents_stats': users_stats,  # Keeping same template variable name for compatibility
        'total_agents': total_users,
        'total_quitus': total_quitus,
        'avg_per_agent': round(avg_per_user, 2),
        'most_productive': most_productive,
        'least_productive': least_productive,
        'period': period,
        'show_inactive': show_inactive,
    }
    
    # Enregistrer la consultation
    AuditLogger.log_action(
        request,
        'VIEW_STATS',
        quitus=None,
        details=f"Consultation des statistiques agents (période: {days} jours)"
    )
    
    return render(request, 'quitus_app/dashboard_stats.html', context)


@login_required(login_url='login')
def notifications_dashboard(request):
    """
    Tableau de bord des notifications email
    Affiche l'historique des notifications avec filtres et statistiques
    """
    from datetime import datetime, timedelta
    
    # Récupérer toutes les notifications
    notifications = HistoriqueNotifications.objects.select_related('quitus').all().order_by('-created_at')
    
    # Filtrer par utilisateur si c'est un agent (pas chef/admin)
    if not (request.user.is_staff or request.user.is_superuser):
        # Les agents voient uniquement les notifications de leurs quitus
        notifications = notifications.filter(quitus__created_by=request.user)
    
    # Filtres
    status_filter = request.GET.get('status', '').strip()
    type_filter = request.GET.get('type', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    search_email = request.GET.get('email', '').strip()
    
    if status_filter:
        notifications = notifications.filter(status=status_filter)
    
    if type_filter:
        notifications = notifications.filter(notification_type=type_filter)
    
    if search_email:
        notifications = notifications.filter(recipient_email__icontains=search_email)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            notifications = notifications.filter(created_at__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            notifications = notifications.filter(created_at__lte=date_to_obj + timedelta(days=1))
        except ValueError:
            pass
    
    # Statistiques globales
    total_notifications = HistoriqueNotifications.objects.count()
    stats = {
        'total': total_notifications,
        'sent': HistoriqueNotifications.objects.filter(status='SENT').count(),
        'pending': HistoriqueNotifications.objects.filter(status='PENDING').count(),
        'failed': HistoriqueNotifications.objects.filter(status='FAILED').count(),
        'bounced': HistoriqueNotifications.objects.filter(status='BOUNCED').count(),
    }
    
    # Statistiques par type
    stats_by_type = HistoriqueNotifications.objects.values('notification_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Pagination
    paginator = Paginator(notifications, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Types et statuts disponibles pour les filtres
    notification_types = HistoriqueNotifications.NOTIFICATION_TYPES
    status_choices = HistoriqueNotifications.STATUS_CHOICES
    
    context = {
        'notifications': page_obj,
        'stats': stats,
        'stats_by_type': stats_by_type,
        'notification_types': notification_types,
        'status_choices': status_choices,
        'filters': {
            'status': status_filter,
            'type': type_filter,
            'date_from': date_from,
            'date_to': date_to,
            'email': search_email,
        },
        'paginator': paginator,
    }
    
    # Log la consultation
    AuditLogger.log_action(
        request,
        'VIEW_NOTIFICATIONS',
        quitus=None,
        details=f"Consultation du tableau de bord notifications ({notifications.count()} résultats)"
    )
    
    return render(request, 'quitus_app/notifications.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def retry_notification(request, notification_id):
    """
    Retenter l'envoi d'une notification échouée
    """
    try:
        notification = HistoriqueNotifications.objects.get(id=notification_id)
        
        # Vérifier que la notification a échoué
        if notification.status not in ['FAILED', 'PENDING']:
            messages.warning(request, f"Cette notification a déjà le statut '{notification.get_status_display()}'.")
            return redirect('notifications_dashboard')
        
        # Retenter l'envoi
        success = NotificationManager._send_email(
            recipient_email=notification.recipient_email,
            subject=notification.subject,
            message_text=notification.message_text,
            message_html=notification.message_html,
            notification_id=notification.id
        )
        
        if success:
            notification.status = 'SENT'
            notification.sent_at = datetime.now()
            notification.save()
            messages.success(request, f"✅ Notification renvoyée avec succès à {notification.recipient_email}")
            
            # Log l'action
            AuditLogger.log_action(
                request,
                'RETRY_NOTIFICATION',
                quitus=notification.quitus,
                details=f"Notification #{notification.id} renvoyée à {notification.recipient_email}"
            )
        else:
            notification.retry_count += 1
            notification.save()
            messages.error(request, f"❌ Échec de l'envoi. Tentative #{notification.retry_count}")
        
    except HistoriqueNotifications.DoesNotExist:
        messages.error(request, "Notification introuvable.")
    except Exception as e:
        messages.error(request, f"Erreur : {str(e)}")
    
    return redirect('notifications_dashboard')


@login_required(login_url='login')
@require_http_methods(["POST"])
def retry_all_failed_notifications(request):
    """
    Retenter l'envoi de toutes les notifications échouées
    """
    try:
        result = NotificationManager.retry_failed_notifications()
        
        if result > 0:
            messages.success(request, f"✅ {result} notification(s) renvoyée(s) avec succès")
        else:
            messages.info(request, "Aucune notification à renvoyer ou toutes les tentatives ont échoué")
        
        # Log l'action
        AuditLogger.log_action(
            request,
            'RETRY_ALL_NOTIFICATIONS',
            quitus=None,
            details=f"Tentative de renvoi de toutes les notifications échouées - {result} succès"
        )
        
    except Exception as e:
        messages.error(request, f"Erreur : {str(e)}")
    
    return redirect('notifications_dashboard')


@login_required(login_url='login')
def expiry_monitor(request):
    """
    Suivi des dates d'expiration des quitus avec code couleur
    - Vert : Plus de 7 jours avant expiration
    - Jaune : 1 à 7 jours avant expiration
    - Rouge : Expiré ou expire aujourd'hui
    """
    from datetime import date, timedelta
    from dateutil.relativedelta import relativedelta

    today = date.today()

    # We'll use month-based thresholds instead of 7 days.
    # Definitions:
    # - safe (green): more than 4 months remaining
    # - warning (yellow): between 1 and 4 months remaining (inclusive)
    # - critical (red): 1 month or less remaining (or expired)
    # For notification batch we consider the next ~4 months window.

    # Récupérer tous les quitus non annulés (inclut ACTIF et EXPIRE)
    quitus_list = Quitus.objects.exclude(statut='ANNULE').select_related('created_by').order_by('date_validite')
    
    # Filtrer par créateur si spécifié
    agent_filter = request.GET.get('agent', '').strip()
    if agent_filter:
        quitus_list = quitus_list.filter(created_by__id=agent_filter)
    
    # Restreindre aux quitus de l'agent connecté si pas staff
    if not (request.user.is_staff or request.user.is_superuser):
        # Filtrer par l'utilisateur connecté (agent uniquement)
        quitus_list = quitus_list.filter(created_by=request.user)
    
    # Filtre par statut d'expiration
    status_filter = request.GET.get('status', '').strip()
    
    # Catégoriser les quitus avec code couleur
    quitus_categorized = []
    stats = {
        'total': 0,
        'green': 0,  # > 7 jours
        'yellow': 0,  # 1-7 jours
        'red': 0,     # Expiré ou expire aujourd'hui
    }
    
    for quitus in quitus_list:
        days_until_expiry = (quitus.date_validite - today).days

        # Compute exact months remaining using relativedelta
        if days_until_expiry < 0:
            # already expired
            category = 'expired'
            color = 'red'
            status_text = f"Expiré depuis {abs(days_until_expiry)} jour(s)"
            urgency = 'critical'
        else:
            rd = relativedelta(quitus.date_validite, today)
            # full months between today and validity (ignore leftover days)
            total_months = rd.years * 12 + rd.months

            # Decide display mode:
            # - if total_months == 0 -> show days
            # - if 1 <= total_months <= 4 -> show months (warning)
            # - if total_months > 4 -> safe (months)
            months_effective = total_months

            if total_months == 0:
                # less than one month remaining -> show days
                category = 'today'
                color = 'red'
                status_text = f"Expire dans {days_until_expiry} jour(s)"
                urgency = 'critical'
                months_effective = 0
                is_months = False
            elif 1 <= total_months <= 4:
                category = 'warning'
                color = 'yellow'
                status_text = f"Expire dans {months_effective} mois(s)"
                urgency = 'warning'
                is_months = True
            else:
                category = 'safe'
                color = 'green'
                status_text = f"Expire dans {months_effective} mois(s)"
                urgency = 'safe'
                is_months = True
        
        # Vérifier si notification déjà envoyée
        notification_sent = HistoriqueNotifications.objects.filter(
            quitus=quitus,
            notification_type='EXPIRY_WARNING',
            status='SENT'
        ).exists()
        
        quitus_data = {
            'quitus': quitus,
            'days_until_expiry': days_until_expiry,
            'months_effective': months_effective if 'months_effective' in locals() else 0,
            'is_months': locals().get('is_months', False),
            'category': category,
            'color': color,
            'status_text': status_text,
            'urgency': urgency,
            'notification_sent': notification_sent,
        }
        
        # Appliquer le filtre de statut
        if status_filter:
            if status_filter == 'green' and color == 'green':
                quitus_categorized.append(quitus_data)
            elif status_filter == 'yellow' and color == 'yellow':
                quitus_categorized.append(quitus_data)
            elif status_filter == 'red' and color == 'red':
                quitus_categorized.append(quitus_data)
        else:
            quitus_categorized.append(quitus_data)
        
        if color == 'green':
            stats['green'] += 1
        elif color == 'yellow':
            stats['yellow'] += 1
        elif color == 'red':
            stats['red'] += 1
        stats['total'] = stats['green'] + stats['yellow'] + stats['red']
    
    # Pagination
    paginator = Paginator(quitus_categorized, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Liste des utilisateurs pour le filtre (si admin/chef)
    users_list = None
    if request.user.is_staff or request.user.is_superuser:
        # Pour les admins/chefs, on peut filtrer par créateur
        users_list = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    context = {
        'quitus_list': page_obj,
        'stats': stats,
        'users_list': users_list,
        'agent_filter': agent_filter,
        'status_filter': status_filter,
        'paginator': paginator,
        'is_restricted': not (request.user.is_staff or request.user.is_superuser),
    }
    
    # Log la consultation
    AuditLogger.log_action(
        request,
        'VIEW_EXPIRY_MONITOR',
        quitus=None,
        details=f"Consultation du suivi d'expiration ({len(quitus_categorized)} quitus)"
    )
    
    return render(request, 'quitus_app/expiry_monitor.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def send_expiry_notification(request, quitus_id):
    """
    Envoyer manuellement une notification d'expiration pour un quitus
    """
    try:
        quitus = Quitus.objects.get(id=quitus_id)
        
        # Vérifier les permissions (agents ne peuvent notifier que leurs quitus)
        if not (request.user.is_staff or request.user.is_superuser):
            # Vérifier que l'utilisateur est le créateur du quitus
            if quitus.created_by != request.user:
                messages.error(request, "Vous n'avez pas la permission de notifier ce quitus.")
                return redirect('expiry_monitor')
        
        # Déterminer l'email du destinataire
        recipient_email = quitus.email or (quitus.created_by.email if quitus.created_by else None)
        
        if not recipient_email:
            messages.error(request, "Aucun email disponible pour ce quitus.")
            return redirect('expiry_monitor')
        
        # Envoyer la notification
        from .notifications import NotificationManager
        notification = NotificationManager.send_expiry_warning(
            quitus=quitus,
            recipient_email=recipient_email,
            recipient_name=quitus.nom_prenoms
        )
        
        if notification and notification.status == 'SENT':
            messages.success(request, f"✅ Notification envoyée à {recipient_email} pour le quitus {quitus.numero_quitus}")
            
            # Log l'action
            AuditLogger.log_action(
                request,
                'SEND_EXPIRY_NOTIFICATION',
                quitus=quitus,
                details=f"Notification manuelle envoyée à {recipient_email}"
            )
        else:
            messages.error(request, f"❌ Échec de l'envoi de la notification")
        
    except Quitus.DoesNotExist:
        messages.error(request, "Quitus introuvable.")
    except Exception as e:
        messages.error(request, f"Erreur : {str(e)}")
    
    return redirect('expiry_monitor')


@login_required(login_url='login')
@require_http_methods(["POST"])
@role_required('admin_plateforme', 'admin_service')
def send_all_expiry_notifications(request):
    """
    Envoyer des notifications pour tous les quitus expirant dans les 7 jours
    Accessible uniquement aux admins et chefs
    """
    from datetime import date, timedelta
    from .notifications import NotificationManager
    from dateutil.relativedelta import relativedelta

    today = date.today()
    # use relativedelta to get an exact 4-month window
    four_months_later = today + relativedelta(months=4)

    # Récupérer les quitus expirant dans les 4 prochains mois (inclus)
    expiring_quitus = Quitus.objects.filter(
        statut='ACTIF',
        date_validite__lte=four_months_later,
        date_validite__gte=today
    ).select_related('created_by')
    
    sent_count = 0
    failed_count = 0
    
    for quitus in expiring_quitus:
        # Vérifier si notification déjà envoyée aujourd'hui
        already_sent = HistoriqueNotifications.objects.filter(
            quitus=quitus,
            notification_type='EXPIRY_WARNING',
            created_at__date=today
        ).exists()
        
        if already_sent:
            continue
        
        # Déterminer l'email
        recipient_email = quitus.email or (quitus.created_by.email if quitus.created_by else None)
        
        if not recipient_email:
            failed_count += 1
            continue
        
        # Envoyer la notification
        notification = NotificationManager.send_expiry_warning(
            quitus=quitus,
            recipient_email=recipient_email,
            recipient_name=quitus.nom_prenoms
        )
        
        if notification and notification.status == 'SENT':
            sent_count += 1
        else:
            failed_count += 1
    
    # Messages de résultat
    if sent_count > 0:
        messages.success(request, f"✅ {sent_count} notification(s) envoyée(s) avec succès")
    if failed_count > 0:
        messages.warning(request, f"⚠️ {failed_count} notification(s) échouée(s)")
    if sent_count == 0 and failed_count == 0:
        messages.info(request, "ℹ️ Aucune notification à envoyer (déjà envoyées ou aucun quitus à notifier)")
    
    # Log l'action
    AuditLogger.log_action(
        request,
        'SEND_ALL_EXPIRY_NOTIFICATIONS',
        quitus=None,
        details=f"Envoi groupé: {sent_count} succès, {failed_count} échecs"
    )
    
    return redirect('expiry_monitor')


@login_required(login_url='login')
def edit_quitus(request, quitus_id):
    """
    Éditer un quitus existant pour corriger des erreurs de saisie
    """
    try:
        quitus = Quitus.objects.get(id=quitus_id)
    except Quitus.DoesNotExist:
        messages.error(request, "Quitus introuvable.")
        return redirect('liste_quitus')
    
    # Vérifier que le quitus est ACTIF
    if quitus.statut != 'ACTIF':
        messages.error(request, "Seuls les quitus actifs peuvent être édités.")
        return redirect('detail_quitus', numero_quitus=quitus.numero_quitus)
    
    # Vérifier les permissions (agents peuvent éditer seulement leurs quitus)
    if not (request.user.is_staff or request.user.is_superuser):
        if quitus.created_by != request.user:
            messages.error(request, "Vous n'avez pas la permission d'éditer ce quitus.")
            return redirect('detail_quitus', numero_quitus=quitus.numero_quitus)
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        quitus.nom_prenoms = request.POST.get('nom_prenoms', quitus.nom_prenoms)
        quitus.raison_sociale = request.POST.get('raison_sociale', '')
        quitus.cni = request.POST.get('cni', quitus.cni)
        quitus.nationalite = request.POST.get('nationalite', quitus.nationalite)
        quitus.activite = request.POST.get('activite', quitus.activite)
        quitus.compte_pal = request.POST.get('compte_pal', quitus.compte_pal)
        quitus.nif = request.POST.get('nif', quitus.nif)
        quitus.telephone = request.POST.get('telephone', quitus.telephone)
        quitus.email = request.POST.get('email', quitus.email)
        quitus.situation_geo = request.POST.get('situation_geo', quitus.situation_geo)
        quitus.adresse_postale = request.POST.get('adresse_postale', quitus.adresse_postale)
        
        try:
            quitus.save()
            
            # Log l'édition
            AuditLogger.log_action(
                request,
                'EDIT_QUITUS',
                quitus=quitus,
                details=f"Quitus {quitus.numero_quitus} modifié"
            )
            
            messages.success(request, f"✅ Quitus {quitus.numero_quitus} modifié avec succès.")
            return redirect('detail_quitus', numero_quitus=quitus.numero_quitus)
            
        except Exception as e:
            messages.error(request, f"❌ Erreur lors de la modification: {str(e)}")
    
    context = {
        'quitus': quitus,
    }
    return render(request, 'quitus_app/edit_quitus.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def cancel_quitus(request, quitus_id):
    """
    Annuler un quitus (changement de statut à ANNULÉ)
    Réservé aux superusers et chefs de service (Chef_Directeur)
    """
    from .permissions import is_admin_service
    
    # Vérifier les permissions (seulement superuser ou chef_directeur)
    if not (request.user.is_superuser or is_admin_service(request.user)):
        messages.error(request, "Vous n'avez pas la permission d'annuler un quitus. Cette action est réservée aux administrateurs et chefs de service.")
        return redirect('liste_quitus')
    
    try:
        quitus = Quitus.objects.get(id=quitus_id)
    except Quitus.DoesNotExist:
        messages.error(request, "Quitus introuvable.")
        return redirect('liste_quitus')
    
    # Vérifier que le quitus est ACTIF
    if quitus.statut != 'ACTIF':
        messages.error(request, "Ce quitus est déjà annulé ou expiré.")
        return redirect('detail_quitus', numero_quitus=quitus.numero_quitus)
    
    # Récupérer le motif d'annulation
    cancel_reason = request.POST.get('cancel_reason', '').strip()
    
    if not cancel_reason:
        messages.error(request, "Le motif d'annulation est obligatoire.")
        return redirect('detail_quitus', numero_quitus=quitus.numero_quitus)
    
    try:
        # Changer le statut
        quitus.statut = 'ANNULÉ'
        quitus.save()
        
        # Log l'annulation
        AuditLogger.log_action(
            request,
            'CANCEL_QUITUS',
            quitus=quitus,
            details=f"Quitus {quitus.numero_quitus} annulé. Motif: {cancel_reason}"
        )
        
        messages.success(request, f"✅ Quitus {quitus.numero_quitus} annulé avec succès.")
        
    except Exception as e:
        messages.error(request, f"❌ Erreur lors de l'annulation: {str(e)}")
    
    return redirect('detail_quitus', numero_quitus=quitus.numero_quitus)
"""
Utilitaires pour la gestion des permissions et rôles
"""
from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.contrib import messages


def has_role(user, role_name):
    """Vérifier si un utilisateur a un rôle spécifique"""
    if user.is_superuser:
        return True
    return user.groups.filter(name=role_name).exists()


def is_admin_plateforme(user):
    """Admin plateforme (Superuser)"""
    return user.is_superuser


def is_admin_service(user):
    """Chef/Directeur de service"""
    return has_role(user, 'Chef_Directeur') or user.is_superuser


def is_agent(user):
    """Agent standard"""
    return has_role(user, 'Agent') or user.is_superuser or is_admin_service(user)


def role_required(*roles):
    """Décorateur pour vérifier si l'utilisateur a l'un des rôles spécifiés"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            # Superuser a accès à tout
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Vérifier si l'utilisateur a l'un des rôles requis
            for role in roles:
                if role == 'admin_plateforme' and is_admin_plateforme(user):
                    return view_func(request, *args, **kwargs)
                elif role == 'admin_service' and is_admin_service(user):
                    return view_func(request, *args, **kwargs)
                elif role == 'agent' and is_agent(user):
                    return view_func(request, *args, **kwargs)
            
            # Accès refusé
            messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
            return redirect('index')
        
        return wrapper
    return decorator


def admin_required(view_func):
    """Décorateur pour les vues réservées aux administrateurs"""
    return role_required('admin_service')(view_func)


def agent_required(view_func):
    """Décorateur pour les vues réservées aux agents"""
    return role_required('agent')(view_func)

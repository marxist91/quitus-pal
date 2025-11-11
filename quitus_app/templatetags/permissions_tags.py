"""
Template tags pour la vérification des permissions et rôles
"""
from django import template
from quitus_app.permissions import is_admin_plateforme, is_admin_service

register = template.Library()


@register.filter
def has_role(user, role_name):
    """
    Vérifie si un utilisateur a un rôle spécifique
    Usage: {% if user|has_role:'Chef_Directeur' %}
    """
    if user.is_superuser:
        return True
    return user.groups.filter(name=role_name).exists()


@register.simple_tag
def can_cancel_quitus(user):
    """
    Vérifie si un utilisateur peut annuler un quitus
    (Superuser ou Chef_Directeur)
    Usage: {% can_cancel_quitus user as can_cancel %}
    """
    return user.is_superuser or is_admin_service(user)


@register.simple_tag
def can_edit_quitus(user):
    """
    Vérifie si un utilisateur peut éditer un quitus
    (Tous les utilisateurs connectés peuvent éditer, mais la vue vérifie qu'ils éditent leurs propres quitus)
    Usage: {% can_edit_quitus user as can_edit %}
    """
    return user.is_authenticated

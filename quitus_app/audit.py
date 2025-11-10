"""
Module d'audit logging complet pour la sécurité
"""
from datetime import datetime
from django.contrib.auth.models import User
from .models import HistoriqueQuitus
import logging

logger = logging.getLogger('quitus_audit')


class AuditLogger:
    """Classe centralisée pour l'audit logging"""
    
    # Types d'actions
    ACTION_LOGIN = 'LOGIN'
    ACTION_LOGOUT = 'LOGOUT'
    ACTION_CREATE_QUITUS = 'CREATE_QUITUS'
    ACTION_UPDATE_QUITUS = 'UPDATE_QUITUS'
    ACTION_DELETE_QUITUS = 'DELETE_QUITUS'
    ACTION_VIEW_QUITUS = 'VIEW_QUITUS'
    ACTION_EXPORT_CSV = 'EXPORT_CSV'
    ACTION_EXPORT_EXCEL = 'EXPORT_EXCEL'
    ACTION_EXPORT_PDF = 'EXPORT_PDF'
    ACTION_VERIFICATION = 'VERIFICATION'
    ACTION_CHANGE_ROLE = 'CHANGE_ROLE'
    ACTION_FAILED_LOGIN = 'FAILED_LOGIN'
    ACTION_PERMISSION_DENIED = 'PERMISSION_DENIED'
    ACTION_SUSPICIOUS_ACTIVITY = 'SUSPICIOUS_ACTIVITY'
    
    # Niveaux de sécurité
    LEVEL_INFO = 'INFO'
    LEVEL_WARNING = 'WARNING'
    LEVEL_CRITICAL = 'CRITICAL'
    
    @staticmethod
    def log_action(request, action, quitus=None, details='', level=LEVEL_INFO):
        """
        Logger une action utilisateur
        
        Args:
            request: HttpRequest
            action: Type d'action (ACTION_*)
            quitus: Objet Quitus associé (optionnel)
            details: Détails supplémentaires
            level: Niveau de sécurité
        """
        try:
            user = request.user if request.user.is_authenticated else None
            ip_address = AuditLogger.get_client_ip(request)
            
            # Créer l'entrée d'historique avec les champs du modèle
            historique = HistoriqueQuitus.objects.create(
                quitus=quitus,
                action=action,
                utilisateur=user.username if user else 'Anonymous',
                ip_address=ip_address,
                details=details
            )
            
            # Log système
            log_message = f"[{level}] {action} - User: {user.username if user else 'Anonymous'} - IP: {ip_address} - Details: {details}"
            if level == AuditLogger.LEVEL_INFO:
                logger.info(log_message)
            elif level == AuditLogger.LEVEL_WARNING:
                logger.warning(log_message)
            elif level == AuditLogger.LEVEL_CRITICAL:
                logger.critical(log_message)
            
            return historique
        except Exception as e:
            logger.error(f"Erreur lors du logging d'audit: {str(e)}")
            return None
    
    @staticmethod
    def get_client_ip(request):
        """Récupérer l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def log_failed_login(request, username):
        """Logger une tentative de connexion échouée"""
        ip_address = AuditLogger.get_client_ip(request)
        logger.warning(f"FAILED_LOGIN attempt - Username: {username} - IP: {ip_address}")
        
        # Créer une entrée sans quitus
        try:
            HistoriqueQuitus.objects.create(
                quitus=None,
                action=AuditLogger.ACTION_FAILED_LOGIN,
                utilisateur=username,
                ip_address=ip_address,
                details=f"Tentative de connexion échouée pour: {username}"
            )
        except Exception as e:
            logger.error(f"Erreur lors du logging de tentative échouée: {str(e)}")
    
    @staticmethod
    def log_permission_denied(request, view_name):
        """Logger une tentative d'accès non autorisé"""
        ip_address = AuditLogger.get_client_ip(request)
        user = request.user.username if request.user.is_authenticated else 'Anonymous'
        logger.warning(f"PERMISSION_DENIED - User: {user} - View: {view_name} - IP: {ip_address}")
        
        try:
            HistoriqueQuitus.objects.create(
                quitus=None,
                action=AuditLogger.ACTION_PERMISSION_DENIED,
                utilisateur=user,
                ip_address=ip_address,
                details=f"Accès non autorisé à: {view_name}"
            )
        except Exception as e:
            logger.error(f"Erreur lors du logging de permission refusée: {str(e)}")
    
    @staticmethod
    def log_suspicious_activity(request, activity_type, details=''):
        """Logger une activité suspecte"""
        ip_address = AuditLogger.get_client_ip(request)
        user = request.user.username if request.user.is_authenticated else 'Anonymous'
        logger.critical(f"SUSPICIOUS_ACTIVITY - Type: {activity_type} - User: {user} - IP: {ip_address}")
        
        try:
            HistoriqueQuitus.objects.create(
                quitus=None,
                action=AuditLogger.ACTION_SUSPICIOUS_ACTIVITY,
                utilisateur=user,
                ip_address=ip_address,
                details=f"Activité suspecte - {activity_type}: {details}"
            )
        except Exception as e:
            logger.error(f"Erreur lors du logging d'activité suspecte: {str(e)}")

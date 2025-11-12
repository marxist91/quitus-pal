"""
Middleware de sécurité avancée
- Rate limiting sur les tentatives de login
- Détection d'activités suspectes
- Protection CSRF/XSS renforcée
"""
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.conf import settings
from .audit import AuditLogger
import logging
import os

logger = logging.getLogger('quitus_security')

# Configuration du rate limiting
LOGIN_ATTEMPTS_LIMIT = 5  # Max 5 tentatives
LOGIN_ATTEMPTS_WINDOW = 15 * 60  # Fenêtre de 15 minutes
SUSPICIOUS_REQUEST_LIMIT = 20  # Max 20 requêtes suspectes

# Désactiver le rate limiting en développement si DISABLE_RATE_LIMIT=True dans .env
DISABLE_RATE_LIMIT = os.getenv('DISABLE_RATE_LIMIT', 'False') == 'True'


class RateLimitMiddleware(MiddlewareMixin):
    """Middleware pour le rate limiting"""
    
    def process_request(self, request):
        # Si DISABLE_RATE_LIMIT=True, ne pas appliquer la limitation
        if DISABLE_RATE_LIMIT:
            return None
            
        # Vérifier le rate limiting sur la page de login
        if request.path == '/login/':
            client_ip = self.get_client_ip(request)
            cache_key = f'login_attempts_{client_ip}'
            attempts = cache.get(cache_key, 0)
            
            if attempts >= LOGIN_ATTEMPTS_LIMIT:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                AuditLogger.log_suspicious_activity(
                    request,
                    'RATE_LIMIT_EXCEEDED',
                    f'Trop de tentatives de connexion depuis {client_ip}'
                )
                return HttpResponseForbidden(
                    "Trop de tentatives de connexion. Veuillez réessayer dans 15 minutes."
                )
            
            # Incrémenter le compteur si POST (tentative de connexion)
            if request.method == 'POST':
                cache.set(cache_key, attempts + 1, LOGIN_ATTEMPTS_WINDOW)
        
        return None
    
    @staticmethod
    def get_client_ip(request):
        """Récupérer l'IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware pour ajouter les en-têtes de sécurité"""
    
    def process_response(self, request, response):
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; "
            "img-src 'self' data:; "
            "font-src 'self' cdnjs.cloudflare.com; "
            "connect-src 'self';"
        )
        
        # Empêcher le clickjacking
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Empêcher le MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Activer la protection XSS du navigateur
        response['X-XSS-Protection'] = '1; mode=block'
        
        # HSTS (HTTPS only) - à activer en production
        # response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


class SuspiciousActivityMiddleware(MiddlewareMixin):
    """Middleware pour détecter les activités suspectes"""
    
    SUSPICIOUS_PATTERNS = [
        '../',  # Path traversal
        '..\\',
        'script>',  # XSS injection
        'onclick=',
        'onerror=',
        'javascript:',
        'union select',  # SQL injection
        'drop table',
        'delete from',
        '<?php',  # PHP injection
        '<%',  # ASP injection
    ]
    
    def process_request(self, request):
        # Vérifier les patterns suspects dans l'URL et les paramètres GET/POST
        suspect_found = False
        pattern_found = ''
        
        # Vérifier l'URL
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern.lower() in request.path.lower():
                suspect_found = True
                pattern_found = pattern
                break
        
        # Vérifier les paramètres GET
        if not suspect_found and request.GET:
            for key, value in request.GET.items():
                for pattern in self.SUSPICIOUS_PATTERNS:
                    if pattern.lower() in str(value).lower():
                        suspect_found = True
                        pattern_found = pattern
                        break
        
        # Vérifier les données POST (sauf fichiers)
        if not suspect_found and request.method == 'POST' and request.POST:
            for key, value in request.POST.items():
                for pattern in self.SUSPICIOUS_PATTERNS:
                    if pattern.lower() in str(value).lower():
                        suspect_found = True
                        pattern_found = pattern
                        break
        
        if suspect_found:
            logger.critical(f"Suspicious pattern detected: {pattern_found} from IP: {self.get_client_ip(request)}")
            AuditLogger.log_suspicious_activity(
                request,
                'INJECTION_ATTEMPT',
                f'Pattern détecté: {pattern_found}'
            )
            return HttpResponseForbidden("Requête suspecte détectée et bloquée.")
        
        return None
    
    @staticmethod
    def get_client_ip(request):
        """Récupérer l'IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

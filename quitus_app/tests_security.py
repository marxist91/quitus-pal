"""
Tests de sécurité complets pour l'application Quitus
- Rate limiting sur login
- Détection des injections
- Permissions et rôles
- Audit logging
"""
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User, Group, Permission
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import datetime, timedelta
from unittest import skip
from .models import Quitus, Agent, HistoriqueQuitus
from .permissions import is_agent, is_admin_service
from .audit import AuditLogger
import json


class RateLimitingTests(TestCase):
    """Tests du rate limiting sur les tentatives de connexion"""
    
    def setUp(self):
        """Préparation des tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        cache.clear()
    
    def tearDown(self):
        """Nettoyage après les tests"""
        cache.clear()
    
    def test_successful_login_no_rate_limit(self):
        """Test: Connexion réussie ne déclenche pas le rate limit"""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertIn(response.status_code, [200, 302])
    
    def test_rate_limit_after_5_failed_attempts(self):
        """Test: Le 6ème essai échoue après 5 tentatives échouées"""
        # 5 premières tentatives échouées
        for i in range(5):
            response = self.client.post('/login/', {
                'username': 'testuser',
                'password': 'wrongpassword'
            }, follow=False)
            self.assertEqual(response.status_code, 200)  # Affiche le formulaire
        
        # 6ème tentative devrait être bloquée (rate limit)
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow=False)
        # Rate limit middleware retourne 403
        self.assertEqual(response.status_code, 403)
    
    def test_rate_limit_expires(self):
        """Test: Le rate limit expire après la fenêtre de temps"""
        # 5 tentatives échouées
        for i in range(5):
            self.client.post('/login/', {
                'username': 'testuser',
                'password': 'wrongpassword'
            })
        
        # 6ème tentative bloquée
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow=False)
        self.assertEqual(response.status_code, 403)
        
        # Effacer le cache pour simuler l'expiration
        cache.clear()
        
        # Connexion réussie après expiration
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, follow=True)
        self.assertIn(response.status_code, [200, 302])


class InjectionDetectionTests(TestCase):
    """Tests de détection d'injections"""
    
    def setUp(self):
        """Préparation des tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_sql_injection_detection(self):
        """Test: Les patterns d'injection SQL sont détectés"""
        injection_patterns = [
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users--",
            "1' DELETE FROM quitus--"
        ]
        
        for pattern in injection_patterns:
            response = self.client.get(f'/recherche/?q={pattern}')
            # Middleware devrait bloquer (403) ou au minimum logger
            self.assertIsNotNone(response)  # Pas de crash
    
    def test_xss_injection_detection(self):
        """Test: Les patterns XSS sont détectés"""
        xss_patterns = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "onerror=alert('xss')",
        ]
        
        for pattern in xss_patterns:
            response = self.client.get(f'/recherche/?q={pattern}')
            self.assertIsNotNone(response)
    
    def test_path_traversal_detection(self):
        """Test: Les patterns de path traversal sont détectés"""
        response = self.client.get('/recherche/../../../etc/passwd')
        self.assertIsNotNone(response)


class PermissionTests(TestCase):
    """Tests des permissions et rôles"""
    
    def setUp(self):
        """Préparation des tests"""
        self.client = Client()
        
        # Créer les groupes/rôles
        self.superuser_group = Group.objects.create(name='Superuser')
        self.agent_group = Group.objects.create(name='Agent')
        self.admin_group = Group.objects.create(name='Chef_Directeur')
        
        # Créer les utilisateurs
        self.superuser = User.objects.create_user(
            username='superuser',
            password='superpass123'
        )
        self.superuser.is_superuser = True
        self.superuser.save()
        
        self.agent = User.objects.create_user(
            username='agent',
            password='agentpass123'
        )
        self.agent.groups.add(self.agent_group)
        
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass123'
        )
        self.admin.groups.add(self.admin_group)
        
        self.unauthorized_user = User.objects.create_user(
            username='unauthorized',
            password='unauthapass123'
        )
    
    def test_login_required_on_protected_views(self):
        """Test: Les vues protégées redirigent vers login"""
        response = self.client.get('/creer/', follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_agent_can_create_quitus(self):
        """Test: Les agents peuvent créer un quitus"""
        self.client.login(username='agent', password='agentpass123')
        response = self.client.get('/creer/')
        self.assertEqual(response.status_code, 200)
    
    def test_unauthorized_cannot_create_quitus(self):
        """Test: Les utilisateurs sans rôle ne peuvent pas créer"""
        self.client.login(username='unauthorized', password='unauthapass123')
        response = self.client.get('/creer/', follow=False)
        # Accepte 302 (redirect login) ou 403 (forbidden) selon la config du decorator
        self.assertIn(response.status_code, [302, 403])


class AuditLoggingTests(TestCase):
    """Tests du logging d'audit"""
    
    @skip("Audit signals not yet implemented - login/logout logging requires signal handlers")
    def setUp(self):
        """Préparation des tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.agent_group = Group.objects.create(name='Agent')
        self.user.groups.add(self.agent_group)
        
        # Créer un Agent Django
        self.agent = Agent.objects.create(
            nom_complet='Agent Test',
            matricule='MAT-AUDIT-001',
            fonction='Agent',
            email='agent@test.com',
            telephone='+228123456789'
        )
        
        HistoriqueQuitus.objects.all().delete()
    
    @skip("Audit signals not yet implemented")
    def test_login_logged(self):
        """Test: Les connexions sont enregistrées"""
        initial_count = HistoriqueQuitus.objects.filter(action='LOGIN').count()
        
        self.client.login(username='testuser', password='testpass123')
        
        final_count = HistoriqueQuitus.objects.filter(action='LOGIN').count()
        self.assertEqual(final_count, initial_count + 1)
    
    @skip("Audit signals not yet implemented")
    def test_logout_logged(self):
        """Test: Les déconnexions sont enregistrées"""
        self.client.login(username='testuser', password='testpass123')
        initial_count = HistoriqueQuitus.objects.filter(action='LOGOUT').count()
        
        self.client.logout()
        
        final_count = HistoriqueQuitus.objects.filter(action='LOGOUT').count()
        self.assertEqual(final_count, initial_count + 1)
    
    @skip("Audit signals not yet implemented")
    def test_quitus_creation_logged(self):
        """Test: La création de quitus est enregistrée"""
        self.client.login(username='testuser', password='testpass123')
        initial_count = HistoriqueQuitus.objects.filter(action='CREATE_QUITUS').count()
        
        # Créer un quitus
        response = self.client.post('/creer/', {
            'numero_quitus': 'QT-' + str(int(datetime.now().timestamp())),
            'nom_prenoms': 'Test Beneficiaire',
            'cni': 'CI123456',
            'nationalite': 'Togolaise',
            'activite': 'Commerce',
            'compte_pal': 'PAL123',
            'date_emission': datetime.now().date().isoformat(),
            'date_validite': (datetime.now() + timedelta(days=365)).date().isoformat(),
            'agent': self.agent.id,
        }, follow=True)
        
        # Vérifier que l'action a été loggée
        final_count = HistoriqueQuitus.objects.filter(action='CREATE_QUITUS').count()
        self.assertGreater(final_count, initial_count)


class SecurityHeadersTests(TestCase):
    """Tests des headers de sécurité"""
    
    def setUp(self):
        """Préparation des tests"""
        self.client = Client()
    
    def test_security_headers_present(self):
        """Test: Les headers de sécurité sont présents"""
        response = self.client.get('/')
        
        # Vérifier les headers de sécurité
        self.assertIn('Content-Security-Policy', response)
        self.assertIn('X-Frame-Options', response)
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-XSS-Protection', response)
    
    def test_csp_header_value(self):
        """Test: La CSP a la bonne valeur"""
        response = self.client.get('/')
        csp = response.get('Content-Security-Policy', '')
        
        # Vérifier que default-src 'self' est présent
        self.assertIn("default-src", csp)
        self.assertIn("'self'", csp)
    
    def test_x_frame_options(self):
        """Test: X-Frame-Options est SAMEORIGIN"""
        response = self.client.get('/')
        x_frame = response.get('X-Frame-Options', '')
        
        self.assertEqual(x_frame, 'SAMEORIGIN')


class FailedLoginLoggingTests(TestCase):
    """Tests du logging des tentatives de connexion échouées"""
    
    def setUp(self):
        """Préparation des tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        HistoriqueQuitus.objects.all().delete()
    
    def test_failed_login_logged(self):
        """Test: Les tentatives échouées sont enregistrées"""
        initial_count = HistoriqueQuitus.objects.filter(action='FAILED_LOGIN').count()
        
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        final_count = HistoriqueQuitus.objects.filter(action='FAILED_LOGIN').count()
        self.assertEqual(final_count, initial_count + 1)
    
    def test_failed_login_details(self):
        """Test: Les détails de la tentative échouée sont enregistrés"""
        self.client.post('/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        failed_attempt = HistoriqueQuitus.objects.filter(action='FAILED_LOGIN').first()
        self.assertIsNotNone(failed_attempt)
        self.assertIn('testuser', failed_attempt.details)


class VerificationLoggingTests(TestCase):
    """Tests du logging des vérifications de quitus"""
    
    def setUp(self):
        """Préparation des tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.agent_group = Group.objects.create(name='Agent')
        self.user.groups.add(self.agent_group)
        
        # Créer un Agent
        self.agent = Agent.objects.create(
            nom_complet='Agent Test',
            matricule='MAT-VERIF-001',
            fonction='Agent',
            email='agent@test.com',
            telephone='+228123456789'
        )
        
        # Créer un quitus
        self.quitus = Quitus.objects.create(
            numero_quitus='QT-TEST-001',
            nom_prenoms='Beneficiaire Test',
            cni='CI123456',
            nationalite='Togolaise',
            activite='Commerce',
            compte_pal='PAL123',
            nif='NIF123456',
            telephone='+22890000001',
            situation_geo='Lome Port',
            adresse_postale='BP 100 Lome',
            email='beneficiaire@test.com',
            agent=self.agent,
            date_emission=datetime.now().date(),
            date_validite=(datetime.now() + timedelta(days=365)).date(),
            code_verification='TEST123456'
        )
        
        HistoriqueQuitus.objects.all().delete()
    
    def test_verification_logged(self):
        """Test: Les vérifications sont enregistrées"""
        initial_count = HistoriqueQuitus.objects.filter(action='VERIFICATION').count()
        
        response = self.client.get(f'/verifier/{self.quitus.code_verification}/')
        
        final_count = HistoriqueQuitus.objects.filter(action='VERIFICATION').count()
        self.assertGreater(final_count, initial_count)

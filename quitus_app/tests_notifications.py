"""
Tests pour le système de notifications par email - Phase 7
"""
from django.test import TestCase, override_settings
from django.core import mail
from django.contrib.auth.models import User, Group
from datetime import datetime, timedelta, date
from .models import Quitus, Agent, HistoriqueNotifications
from .notifications import NotificationManager, NotificationChecker


class EmailNotificationTests(TestCase):
    """Tests du système de notifications email"""
    
    def setUp(self):
        """Préparation des tests"""
        # Créer agent
        self.agent = Agent.objects.create(
            nom_complet='Agent Togo',
            matricule='MAT001',
            fonction='Agent',
            email='agent@test.com',
            telephone='+228123456789'
        )
        
        # Créer quitus expirant dans 7 jours
        expiry_date = date.today() + timedelta(days=7)
        self.expiring_quitus = Quitus.objects.create(
            numero_quitus='QT-EXPIRING-001',
            nom_prenoms='Jean Dupont',
            cni='CI123456',
            nationalite='Togolaise',
            activite='Commerce',
            compte_pal='PAL123',
            email='beneficiaire@test.com',
            nif='NIF123456',
            telephone='+22890000000',
            situation_geo='Lome Port',
            adresse_postale='BP 100 Lome',
            agent=self.agent,
            date_emission=date.today(),
            date_validite=expiry_date,
        )
        
        # Créer quitus expiré
        self.expired_quitus = Quitus.objects.create(
            numero_quitus='QT-EXPIRED-001',
            nom_prenoms='Marie Martin',
            cni='CI654321',
            nationalite='Togolaise',
            activite='Services',
            compte_pal='PAL456',
            email='marie@test.com',
            nif='NIF654321',
            telephone='+22891111111',
            situation_geo='Zone Industrielle',
            adresse_postale='BP 200 Lome',
            agent=self.agent,
            date_emission=date.today() - timedelta(days=30),
            date_validite=date.today() - timedelta(days=1),
        )
        # Vider la boîte email à chaque test
        mail.outbox.clear()

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_expiry_warning_notification(self):
        """Test: Envoi d'une notification d'avertissement d'expiration"""
        notification = NotificationManager.send_expiry_warning(
            quitus=self.expiring_quitus,
            recipient_email='beneficiaire@test.com',
            recipient_name='Jean Dupont'
        )
        
        # Vérifier que la notification a été créée
        self.assertIsNotNone(notification)
        self.assertEqual(notification.notification_type, 'EXPIRY_WARNING')
        self.assertEqual(notification.recipient_email, 'beneficiaire@test.com')
        self.assertEqual(notification.status, 'SENT')
        
        # Vérifier que l'email a été envoyé
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Avertissement', mail.outbox[0].subject)
        self.assertIn('Jean Dupont', mail.outbox[0].body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_notification_recorded_in_database(self):
        """Test: La notification est enregistrée dans la base de données"""
        NotificationManager.send_expiry_warning(
            quitus=self.expiring_quitus,
            recipient_email='test@example.com',
            recipient_name='Test User'
        )
        
        # Vérifier que la notification existe en base
        notification = HistoriqueNotifications.objects.get(
            quitus=self.expiring_quitus,
            notification_type='EXPIRY_WARNING'
        )
        
        self.assertEqual(notification.recipient_email, 'test@example.com')
        self.assertEqual(notification.status, 'SENT')
        self.assertIsNotNone(notification.sent_at)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_check_expiring_quitus_finds_candidates(self):
        """Test: check_expiring_quitus trouve les quitus expirant dans 7 jours"""
        result = NotificationChecker.check_expiring_quitus(days_before=7)
        
        # Au moins le quitus de test doit être trouvé
        self.assertGreater(result['checked'], 0)
        self.assertGreater(result['notified'], 0)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_no_duplicate_notifications(self):
        """Test: Pas d'envoi de notification en double le même jour"""
        # Première envoi
        NotificationManager.send_expiry_warning(
            quitus=self.expiring_quitus,
            recipient_email='dup@test.com',
            recipient_name='Test'
        )
        # Vider outbox pour compter seulement les envois supplémentaires
        mail.outbox.clear()
        
        # Vérifier déduplication lors de check_expiring_quitus
        result = NotificationChecker.check_expiring_quitus(days_before=7)
        
        # Aucun nouvel email ne doit être envoyé
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_notification_with_missing_email(self):
        """Test: Gestion des quitus sans email"""
        quitus_no_email = Quitus.objects.create(
            numero_quitus='QT-NO-EMAIL-001',
            nom_prenoms='No Email User',
            cni='CI999999',
            nationalite='Togolaise',
            activite='Test',
            compte_pal='PAL999',
            # email non fourni
            nif='NIF999999',
            telephone='+22892222222',
            situation_geo='Lieu inconnu',
            adresse_postale='BP 300 Lome',
            agent=self.agent,
            date_emission=date.today(),
            date_validite=date.today() + timedelta(days=7),
        )
        
        # Essayer d'envoyer notification
        notification = NotificationManager.send_expiry_warning(
            quitus=quitus_no_email,
            recipient_email=None,
            recipient_name='Test'
        )
        
        # Aucun email ne doit être envoyé
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_notification_properties(self):
        """Test: Les propriétés des notifications fonctionnent correctement"""
        notification = NotificationManager.send_expiry_warning(
            quitus=self.expiring_quitus,
            recipient_email='test@test.com',
            recipient_name='Test'
        )
        
        # Vérifier les propriétés
        self.assertTrue(notification.is_sent)
        self.assertFalse(notification.is_pending)
        self.assertEqual(notification.days_since_created, 0)


class NotificationRetryTests(TestCase):
    """Tests pour la retentative d'envoi des notifications échouées"""

    def setUp(self):
        """Préparation des tests"""
        self.agent = Agent.objects.create(
            nom_complet='Agent Test',
            matricule='MAT002',
            fonction='Agent',
            email='agent@test.com',
            telephone='+228987654321'
        )
        
        self.quitus = Quitus.objects.create(
            numero_quitus='QT-RETRY-001',
            nom_prenoms='Retry Test',
            cni='CI111111',
            nationalite='Togolaise',
            activite='Test',
            compte_pal='PAL111',
            email='retry@test.com',
            nif='NIF111111',
            telephone='+22893333333',
            situation_geo='Site Retry',
            adresse_postale='BP 400 Lome',
            agent=self.agent,
            date_emission=date.today(),
            date_validite=date.today() + timedelta(days=7),
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_failed_notification_can_be_retried(self):
        """Test: Une notification échouée peut être renvoyée"""
        # Créer une notification échouée
        notification = HistoriqueNotifications.objects.create(
            quitus=self.quitus,
            notification_type='EXPIRY_WARNING',
            recipient_email='retry@test.com',
            status='FAILED',
            subject='Test',
            message_text='Test message',
            message_html='<p>Test message</p>',
            retry_count=0
        )
        
        # Retenter l'envoi
        result = NotificationManager.retry_failed_notifications()
        
        # La notification doit avoir été renvoyée
        self.assertEqual(result, 1)
        # Vérifier que l'email a été envoyé
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_max_retry_limit(self):
        """Test: Les tentatives sont limitées par NOTIFICATION_MAX_RETRIES"""
        from django.conf import settings
        
        # Créer une notification avec trop de tentatives
        notification = HistoriqueNotifications.objects.create(
            quitus=self.quitus,
            notification_type='EXPIRY_WARNING',
            recipient_email='retry@test.com',
            status='FAILED',
            subject='Test',
            message_text='Test',
            message_html='<p>Test</p>',
            retry_count=settings.NOTIFICATION_MAX_RETRIES
        )
        
        # Tentative de retry
        result = NotificationManager.retry_failed_notifications()
        # Aucun email ne doit être envoyé (limite atteinte)
        self.assertEqual(result, 0)
        self.assertEqual(len(mail.outbox), 0)


class NotificationModelTests(TestCase):
    """Tests du modèle HistoriqueNotifications"""

    def setUp(self):
        """Préparation des tests"""
        self.agent = Agent.objects.create(
            nom_complet='Agent Test',
            matricule='MAT003',
            fonction='Agent',
            email='agent@test.com',
            telephone='+228555555555'
        )
        
        self.quitus = Quitus.objects.create(
            numero_quitus='QT-MODEL-001',
            nom_prenoms='Model Test',
            cni='CI222222',
            nationalite='Togolaise',
            activite='Test',
            compte_pal='PAL222',
            email='model@test.com',
            nif='NIF222222',
            telephone='+22894444444',
            situation_geo='Site Model',
            adresse_postale='BP 500 Lome',
            agent=self.agent,
            date_emission=date.today(),
            date_validite=date.today() + timedelta(days=7),
        )

    def test_notification_creation(self):
        """Test: Création d'une notification"""
        notification = HistoriqueNotifications.objects.create(
            quitus=self.quitus,
            notification_type='EXPIRY_WARNING',
            recipient_email='test@test.com',
            recipient_name='Test User',
            status='SENT',
            subject='Test Subject',
            message_text='Test message',
        )
        
        self.assertEqual(notification.status, 'SENT')
        self.assertEqual(notification.notification_type, 'EXPIRY_WARNING')
        self.assertIsNotNone(notification.created_at)

    def test_notification_status_choices(self):
        """Test: Les choix de statut fonctionnent"""
        statuses = ['PENDING', 'SENT', 'FAILED', 'BOUNCED']
        
        for status in statuses:
            notification = HistoriqueNotifications.objects.create(
                quitus=self.quitus,
                notification_type='EXPIRY_WARNING',
                recipient_email=f'{status}@test.com',
                status=status,
                subject='Test',
                message_text='Test',
            )
            
            self.assertEqual(notification.status, status)

    def test_notification_string_representation(self):
        """Test: La représentation en chaîne de la notification"""
        notification = HistoriqueNotifications.objects.create(
            quitus=self.quitus,
            notification_type='EXPIRY_WARNING',
            recipient_email='test@test.com',
            status='SENT',
            subject='Test',
            message_text='Test',
        )
        
        str_repr = str(notification)
        self.assertIn('Avertissement d\'expiration', str_repr)
        self.assertIn('test@test.com', str_repr)
        self.assertIn('SENT', str_repr)

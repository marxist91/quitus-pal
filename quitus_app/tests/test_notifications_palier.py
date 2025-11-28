from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
from dateutil.relativedelta import relativedelta

from quitus_app.models import Quitus
from quitus_app.notifications import NotificationManager


class NotificationPalierSelectionTest(TestCase):
    """Vérifie la sélection de template/sujet selon les paliers de notification"""

    def _create_quitus(self, numero, date_validite):
        return Quitus.objects.create(
            numero_quitus=numero,
            date_validite=date_validite,
            nom_prenoms='Test User',
            cni='C12345678',
            activite='Test Activity',
            compte_pal='C000001',
            nif='NIF123',
            telephone='+22800000000',
            email='test@example.com',
            situation_geo='Port',
            adresse_postale='Adresse',
        )

    @patch.object(NotificationManager, '_send_email', return_value=True)
    def test_expired_selects_expired_template(self, _send):
        today = timezone.now().date()
        q = self._create_quitus('EXP-001', today - relativedelta(days=1))
        notification = NotificationManager.send_expiry_warning(q, q.email, recipient_name=q.nom_prenoms)
        self.assertIsNotNone(notification)
        self.assertTrue(notification.subject.startswith('Quitus expiré'))
        self.assertIn('Information — Quitus expiré', notification.message_html)

    @patch.object(NotificationManager, '_send_email', return_value=True)
    def test_less_than_one_month_selects_days_template(self, _send):
        today = timezone.now().date()
        q = self._create_quitus('LESSTHAN1-001', today + relativedelta(days=15))
        notification = NotificationManager.send_expiry_warning(q, q.email, recipient_name=q.nom_prenoms)
        self.assertIsNotNone(notification)
        self.assertIn('expirera dans 15 jour', notification.subject)
        self.assertIn('Alerte — Quitus presque expiré', notification.message_html)

    @patch.object(NotificationManager, '_send_email', return_value=True)
    def test_one_month_selects_1month_template(self, _send):
        today = timezone.now().date()
        q = self._create_quitus('ONE-001', today + relativedelta(months=1))
        notification = NotificationManager.send_expiry_warning(q, q.email, recipient_name=q.nom_prenoms)
        self.assertIsNotNone(notification)
        self.assertIn('Rappel', notification.subject)
        self.assertIn("Notification — Quitus proche de l'expiration", notification.message_html)

    @patch.object(NotificationManager, '_send_email', return_value=True)
    def test_four_plus_months_selects_4months_template(self, _send):
        today = timezone.now().date()
        q = self._create_quitus('MANY-001', today + relativedelta(months=5))
        notification = NotificationManager.send_expiry_warning(q, q.email, recipient_name=q.nom_prenoms)
        self.assertIsNotNone(notification)
        self.assertIn('5 mois', notification.subject)
        self.assertIn('Rappel — Quitus à échéance', notification.message_html)

    @patch.object(NotificationManager, '_send_email', return_value=True)
    def test_logo_cid_set_when_logo_present(self, _send):
        """Si un fichier de logo existe dans les emplacements connus, le HTML contient `cid:logo`"""
        import os
        from django.conf import settings

        # Créer un fichier logo minimal dans BASE_DIR/static/logo/logo.png
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'logo', 'logo.png')
        os.makedirs(os.path.dirname(logo_path), exist_ok=True)
        try:
            with open(logo_path, 'wb') as f:
                f.write(b'\x89PNG\r\n')

            today = timezone.now().date()
            q = self._create_quitus('LOGO-001', today + relativedelta(months=2))
            notification = NotificationManager.send_expiry_warning(q, q.email, recipient_name=q.nom_prenoms)
            self.assertIsNotNone(notification)
            # Le template doit contenir la référence inline au logo
            self.assertIn('cid:logo', notification.message_html)
        finally:
            try:
                os.remove(logo_path)
            except Exception:
                pass

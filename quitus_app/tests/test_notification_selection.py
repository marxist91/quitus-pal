from django.test import TestCase, override_settings
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from quitus_app.models import Quitus, HistoriqueNotifications
from quitus_app.notifications import NotificationManager


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class NotificationSelectionTests(TestCase):
    def _create_quitus(self, numero, valid_date, email='test@example.local'):
        return Quitus.objects.create(
            numero_quitus=numero,
            date_validite=valid_date,
            date_emission=timezone.now().date(),
            nom_prenoms='Test User',
            cni='C123456',
            activite='Commerce',
            compte_pal='C000001',
            nif='NIF123',
            telephone='+22800000000',
            email=email,
            situation_geo='Port',
            adresse_postale='BP 123'
        )

    def test_expired_selection(self):
        today = timezone.now().date()
        q = self._create_quitus('PAL-EXPIRED-1', today - relativedelta(days=1))
        notif = NotificationManager.send_expiry_warning(q, q.email, recipient_name=q.nom_prenoms)
        self.assertIsNotNone(notif)
        self.assertIn('Quitus expiré', notif.subject)

    def test_less_than_one_month_selection(self):
        today = timezone.now().date()
        q = self._create_quitus('PAL-LESS1-1', today + relativedelta(days=10))
        notif = NotificationManager.send_expiry_warning(q, q.email, recipient_name=q.nom_prenoms)
        self.assertIsNotNone(notif)
        # subject should mention days
        self.assertIn('jour', notif.subject)

    def test_one_month_selection(self):
        today = timezone.now().date()
        q = self._create_quitus('PAL-1M-1', today + relativedelta(months=1))
        notif = NotificationManager.send_expiry_warning(q, q.email, recipient_name=q.nom_prenoms)
        self.assertIsNotNone(notif)
        self.assertTrue(notif.subject.startswith('Rappel') or 'mois' in notif.subject)

    def test_four_months_selection(self):
        today = timezone.now().date()
        q = self._create_quitus('PAL-4M-1', today + relativedelta(months=4))
        notif = NotificationManager.send_expiry_warning(q, q.email, recipient_name=q.nom_prenoms)
        self.assertIsNotNone(notif)
        # Expect a generic months warning
        self.assertIn('Avertissement', notif.subject)

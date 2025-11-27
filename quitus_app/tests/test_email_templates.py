from django.test import TestCase
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from unittest.mock import patch

from quitus_app.models import Quitus
from quitus_app.notifications import NotificationManager


class EmailTemplateMonthsDaysTest(TestCase):
    def setUp(self):
        today = date.today()
        # expiry ~1 month + 7 days from today (ensures months_total == 1 and days_remaining > 30)
        expiry = today + relativedelta(months=1) + timedelta(days=7)

        self.quitus = Quitus.objects.create(
            numero_quitus='PAL-TEST-EMAIL-001',
            date_validite=expiry,
            nom_prenoms='Test User',
            cni='CNI-TEST',
            activite='Test',
            compte_pal='C000999',
            nif='NIF-TEST',
            telephone='+22890000001',
            email='test@example.com',
            situation_geo='Lome',
            adresse_postale='BP 1'
        )

    @patch('quitus_app.notifications.NotificationManager._send_email', return_value=True)
    def test_templates_include_months_and_days(self, mock_send):
        """Vérifie que les templates incluent à la fois les mois et les jours restants."""
        notification = NotificationManager.send_expiry_warning(
            quitus=self.quitus,
            recipient_email='test@example.com',
            recipient_name='Test User'
        )

        self.assertIsNotNone(notification)
        html = notification.message_html or ''
        text = notification.message_text or ''

        # Calculs attendus
        today = date.today()
        days_remaining = (self.quitus.date_validite - today).days
        rd = relativedelta(self.quitus.date_validite, today)
        months_total = rd.years * 12 + rd.months

        # Vérifier la présence de la mention mois et du nombre de jours dans HTML et TXT
        self.assertIn(f"{months_total} mois", html)
        self.assertIn(str(days_remaining), html)
        self.assertIn(f"{months_total} mois", text)
        self.assertIn(str(days_remaining), text)

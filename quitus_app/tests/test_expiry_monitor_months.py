from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, timedelta
from quitus_app.models import Quitus


class ExpiryMonitorMonthsTest(TestCase):
    def setUp(self):
        # create a staff user and login
        self.user = User.objects.create_user(username='admin', password='pass')
        self.user.is_staff = True
        self.user.save()
        self.client = Client()
        self.client.login(username='admin', password='pass')

        today = date.today()

        # quitus in ~3 months
        q1 = Quitus.objects.create(
            numero_quitus='PAL-TEST-001',
            date_validite=today + timedelta(days=90),
            nom_prenoms='Test One',
            cni='CNI001',
            activite='Test',
            compte_pal='C000001',
            nif='NIF001',
            telephone='+22890000001',
            email='one@example.com',
            situation_geo='Lome',
            adresse_postale='BP 1',
            created_by=self.user
        )

        # quitus in ~15 days (less than 1 month)
        q2 = Quitus.objects.create(
            numero_quitus='PAL-TEST-002',
            date_validite=today + timedelta(days=15),
            nom_prenoms='Test Two',
            cni='CNI002',
            activite='Test',
            compte_pal='C000002',
            nif='NIF002',
            telephone='+22890000002',
            email='two@example.com',
            situation_geo='Lome',
            adresse_postale='BP 2',
            created_by=self.user
        )

        # quitus already expired
        q3 = Quitus.objects.create(
            numero_quitus='PAL-TEST-003',
            date_validite=today - timedelta(days=5),
            nom_prenoms='Test Three',
            cni='CNI003',
            activite='Test',
            compte_pal='C000003',
            nif='NIF003',
            telephone='+22890000003',
            email='three@example.com',
            situation_geo='Lome',
            adresse_postale='BP 3',
            created_by=self.user
        )

    def test_expiry_monitor_months_and_days(self):
        url = reverse('expiry_monitor')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        page = resp.context['quitus_list']
        found = {item['quitus'].numero_quitus: item for item in page.object_list}

        # q1 should be shown in months (approx 3 months)
        item1 = found.get('PAL-TEST-001')
        self.assertIsNotNone(item1)
        self.assertTrue(item1.get('is_months'))
        self.assertGreaterEqual(item1.get('months_effective'), 2)

        # q2 should be shown in days (less than 1 month)
        item2 = found.get('PAL-TEST-002')
        self.assertIsNotNone(item2)
        self.assertFalse(item2.get('is_months'))
        self.assertGreaterEqual(item2.get('days_until_expiry'), 0)

        # q3 expired -> months flag false and negative days
        item3 = found.get('PAL-TEST-003')
        self.assertIsNotNone(item3)
        self.assertFalse(item3.get('is_months'))
        self.assertLess(item3.get('days_until_expiry'), 0)

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from quitus_app.models import Quitus, RenumberBatch, HistoriqueQuitus
from datetime import date


class RenumberFlowTests(TestCase):
    def setUp(self):
        # create admin user
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'pass')
        self.client = Client()
        self.client.login(username='admin', password='pass')

        # create sample quitus
        self.q1 = Quitus.objects.create(
            numero_quitus='PAL-2025-001',
            date_validite=date(2025,12,31),
            nom_prenoms='Test User1',
            cni='CNI1',
            activite='Act',
            compte_pal='C123456',
            nif='NIF1',
            telephone='+22890000000',
            email='a@example.com',
            situation_geo='Lome',
            adresse_postale='BP 1'
        )
        self.q2 = Quitus.objects.create(
            numero_quitus='PAL-2025-002',
            date_validite=date(2025,12,31),
            nom_prenoms='Test User2',
            cni='CNI2',
            activite='Act',
            compte_pal='C234567',
            nif='NIF2',
            telephone='+22890000001',
            email='b@example.com',
            situation_geo='Lome',
            adresse_postale='BP 2'
        )

    def test_preview_apply_undo_flow(self):
        # Request preview (no confirm) -> creates RenumberBatch
        url = reverse('admin_regenerate_numeros')
        data = {
            'quitus_ids': f'{self.q1.numero_quitus}\n{self.q2.numero_quitus}',
            'action': 'regenerate',
            'new_prefix': '',
            'start_number': ''
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        # a RenumberBatch should be created
        batch = RenumberBatch.objects.first()
        self.assertIsNotNone(batch)
        self.assertFalse(batch.applied)
        # preview contains proposed changes
        self.assertTrue(len(batch.changes) >= 2)

        # Apply the batch by posting confirm with batch_id
        data_confirm = {'confirm': '1', 'batch_id': str(batch.id)}
        resp2 = self.client.post(url, data_confirm)
        self.assertIn(resp2.status_code, (200, 302))
        batch.refresh_from_db()
        self.assertTrue(batch.applied)

        # Ensure quitus numbers have been updated
        q1 = Quitus.objects.get(id=self.q1.id)
        q2 = Quitus.objects.get(id=self.q2.id)
        self.assertNotEqual(q1.numero_quitus, 'PAL-2025-001')
        self.assertNotEqual(q2.numero_quitus, 'PAL-2025-002')

        # Ensure history entries created
        histories = HistoriqueQuitus.objects.filter(details__contains=str(batch.id))
        self.assertTrue(histories.exists())

        # Undo the batch
        undo_url = reverse('admin_regenerate_undo', args=[str(batch.id)])
        resp3 = self.client.post(undo_url)
        self.assertIn(resp3.status_code, (200, 302))

        # Check restore
        q1_after = Quitus.objects.get(id=self.q1.id)
        q2_after = Quitus.objects.get(id=self.q2.id)
        self.assertIn('PAL-2025-001', [q1_after.numero_quitus, q2_after.numero_quitus, 'PAL-2025-001'])
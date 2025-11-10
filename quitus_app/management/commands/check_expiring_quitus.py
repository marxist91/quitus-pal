"""
Management command pour vérifier et envoyer les notifications d'expiration
Usage: python manage.py check_expiring_quitus [--days N]
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from quitus_app.notifications import NotificationChecker, NotificationManager
import logging

logger = logging.getLogger('quitus_audit')


class Command(BaseCommand):
    help = 'Vérifier et envoyer les notifications pour quitus expirant bientôt'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help=f'Nombre de jours avant expiration (default: {settings.NOTIFICATION_DAYS_BEFORE_EXPIRY})',
        )
        parser.add_argument(
            '--retry',
            action='store_true',
            help='Retenter les notifications échouées',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🚀 Démarrage de la vérification des quitus expirant...'))
        
        try:
            # Retenter les notifications échouées si demandé
            if options['retry']:
                self.stdout.write('🔄 Retentative des notifications échouées...')
                retry_count = NotificationManager.retry_failed_notifications()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {retry_count} notifications renvoyées avec succès')
                )
            
            # Vérifier les quitus expirant
            days = options['days']
            if days is not None:
                self.stdout.write(f'📅 Vérification des quitus expirant dans {days} jours')
            else:
                self.stdout.write(
                    f'📅 Vérification des quitus expirant dans {settings.NOTIFICATION_DAYS_BEFORE_EXPIRY} jours'
                )
            
            result = NotificationChecker.check_expiring_quitus(days_before=days)
            
            # Afficher les résultats
            self.stdout.write('\n' + '='*70)
            self.stdout.write('RÉSULTATS DE LA VÉRIFICATION')
            self.stdout.write('='*70)
            self.stdout.write(f'📊 Quitus vérifiés:        {result["checked"]}')
            self.stdout.write(
                self.style.SUCCESS(f'✅ Notifications envoyées: {result["notified"]}')
            )
            if result['errors'] > 0:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Erreurs rencontrées:    {result["errors"]}')
                )
            self.stdout.write('='*70 + '\n')
            
            logger.info(f"✅ Vérification complétée: {result}")
            
        except Exception as e:
            error_msg = f'❌ Erreur lors de la vérification: {str(e)}'
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(error_msg)
            raise

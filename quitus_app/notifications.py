"""
Module de gestion des notifications email
Handles sending, tracking, and retrying email notifications
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from datetime import datetime, timedelta
import logging

from .models import HistoriqueNotifications, Quitus

logger = logging.getLogger('quitus_audit')


class NotificationManager:
    """Gestionnaire centralisé des notifications"""
    
    @staticmethod
    def send_expiry_warning(quitus, recipient_email, recipient_name=None):
        """
        Envoyer une notification d'avertissement d'expiration
        
        Args:
            quitus: Instance Quitus
            recipient_email: Email du destinataire
            recipient_name: Nom du destinataire (optionnel)
        
        Returns:
            HistoriqueNotifications instance
        """
        try:
            # Calculer les jours restants et les mois restants (précis)
            from dateutil.relativedelta import relativedelta
            today = datetime.now().date()
            days_remaining = (quitus.date_validite - today).days
            rd = relativedelta(quitus.date_validite, today) if days_remaining >= 0 else None
            months_total = 0
            # Do not count partial months as a full month here — keep consistent with expiry_monitor
            if rd:
                months_total = (rd.years * 12) + rd.months
            months_effective = months_total if rd else 0

            # Préparer le contexte commun
            context = {
                'quitus': quitus,
                'recipient_name': recipient_name or 'Bénéficiaire',
                'days_remaining': days_remaining,
                'months_effective': months_effective,
                'expiry_date': quitus.date_validite.strftime('%d/%m/%Y'),
                'notification_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
            }

            # Détecter la présence d'un logo local pour attachement inline
            logo_path = None
            try:
                import os
                candidates = []
                if getattr(settings, 'STATIC_ROOT', None):
                    candidates.append(os.path.join(settings.STATIC_ROOT, 'logo', 'logo.png'))
                if getattr(settings, 'STATICFILES_DIRS', None):
                    for d in settings.STATICFILES_DIRS:
                        candidates.append(os.path.join(d, 'logo', 'logo.png'))
                # Common project locations
                if getattr(settings, 'BASE_DIR', None):
                    candidates.append(os.path.join(settings.BASE_DIR, 'static', 'logo', 'logo.png'))
                    candidates.append(os.path.join(settings.BASE_DIR, 'quitus_app', 'static', 'logo', 'logo.png'))
                    candidates.append(os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png'))
                    candidates.append(os.path.join(settings.BASE_DIR, 'images', 'logo.png'))

                for p in candidates:
                    if p and os.path.exists(p):
                        logo_path = p
                        break
            except Exception:
                logo_path = None

            if logo_path:
                # fournir l'ID du contenu pour que le template puisse utiliser cid:logo
                context['logo_cid'] = 'logo'

            # Choisir modèle et sujet selon le palier
            if days_remaining < 0:
                # expired
                subject = f"Quitus expiré: {quitus.numero_quitus}"
                html_tpl = 'quitus_app/emails/expiry_expired.html'
                txt_tpl = 'quitus_app/emails/expiry_expired.txt'
            else:
                # Use configurable month-based palier if enabled, otherwise fallback to previous logic
                use_months = getattr(settings, 'NOTIFICATION_USE_MONTHS', True)
                paliers = getattr(settings, 'NOTIFICATION_PALIERS_MONTHS', [4, 1, 0])

                chosen = False
                if use_months and paliers:
                    # iterate palier list in order; first match wins
                    for p in paliers:
                        try:
                            p = int(p)
                        except Exception:
                            continue
                        if p <= 0:
                            # less than 1 month -> days template
                            if months_effective <= 0:
                                subject = f"Avertissement: Votre Quitus expirera dans {days_remaining} jour(s)"
                                html_tpl = 'quitus_app/emails/expiry_less1month.html'
                                txt_tpl = 'quitus_app/emails/expiry_less1month.txt'
                                chosen = True
                                break
                            # otherwise continue checking higher paliers
                        else:
                            if months_effective >= p:
                                # map palier to template
                                if p == 1:
                                    subject = f"Rappel: Votre Quitus expirera dans {months_effective} mois"
                                    html_tpl = 'quitus_app/emails/expiry_1month.html'
                                    txt_tpl = 'quitus_app/emails/expiry_1month.txt'
                                else:
                                    # generic months (e.g. 4+ months)
                                    subject = f"Avertissement: Votre Quitus expirera dans {months_effective} mois"
                                    html_tpl = 'quitus_app/emails/expiry_4months.html'
                                    txt_tpl = 'quitus_app/emails/expiry_4months.txt'
                                chosen = True
                                break

                if not chosen:
                    # fallback to original behavior
                    if months_effective <= 0:
                        subject = f"Avertissement: Votre Quitus expirera dans {days_remaining} jour(s)"
                        html_tpl = 'quitus_app/emails/expiry_less1month.html'
                        txt_tpl = 'quitus_app/emails/expiry_less1month.txt'
                    elif months_effective == 1:
                        subject = f"Rappel: Votre Quitus expirera dans {months_effective} mois"
                        html_tpl = 'quitus_app/emails/expiry_1month.html'
                        txt_tpl = 'quitus_app/emails/expiry_1month.txt'
                    else:
                        subject = f"Avertissement: Votre Quitus expirera dans {months_effective} mois"
                        html_tpl = 'quitus_app/emails/expiry_4months.html'
                        txt_tpl = 'quitus_app/emails/expiry_4months.txt'

            # Rendu des templates
            message_html = render_to_string(html_tpl, context)
            message_text = render_to_string(txt_tpl, context)
            
            # Créer l'enregistrement de notification
            notification = HistoriqueNotifications.objects.create(
                quitus=quitus,
                notification_type='EXPIRY_WARNING',
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                status='PENDING',
                subject=subject,
                message_text=message_text,
                message_html=message_html,
            )
            
            # Envoyer l'email
            success = NotificationManager._send_email(
                recipient_email=recipient_email,
                subject=subject,
                message_text=message_text,
                message_html=message_html,
                notification_id=notification.id,
                logo_path=logo_path
            )
            
            if success:
                notification.status = 'SENT'
                notification.sent_at = datetime.now()
                logger.info(f"[OK] Email d'expiration envoye a {recipient_email} pour {quitus.numero_quitus}")
            else:
                notification.status = 'FAILED'
                notification.retry_count = 1
                logger.warning(f"[FAIL] Echec d'envoi email a {recipient_email} pour {quitus.numero_quitus}")
            
            notification.save()
            return notification
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de notification: {str(e)}")
            return None
    
    @staticmethod
    def _send_email(recipient_email, subject, message_text, message_html, notification_id=None, logo_path=None):
        """
        Envoyer un email avec gestion d'erreurs
        
        Args:
            recipient_email: Email destinataire
            subject: Sujet de l'email
            message_text: Version texte
            message_html: Version HTML
            notification_id: ID de la notification (pour logging)
        
        Returns:
            Boolean: True si succès, False sinon
        """
        try:
            # Créer email multi-part
            msg = EmailMultiAlternatives(
                subject=subject,
                body=message_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            
            # Ajouter version HTML
            msg.attach_alternative(message_html, "text/html")

            # Attacher l'image inline si fournie
            if logo_path:
                try:
                    from email.mime.image import MIMEImage
                    import os
                    with open(logo_path, 'rb') as f:
                        img = MIMEImage(f.read())
                        img.add_header('Content-ID', '<logo>')
                        img.add_header('Content-Disposition', 'inline', filename=os.path.basename(logo_path))
                        msg.attach(img)
                except Exception as e:
                    logger.warning(f"Impossible d'attacher le logo inline: {e}")

            # Envoyer
            result = msg.send(fail_silently=False)
            if result:  # result == 1 en succès
                logger.debug(f"Email envoye: {result} messages")
            return bool(result)  # Convertir en boolean
            
        except Exception as e:
            logger.error(f"Erreur d'envoi email (notification #{notification_id}): {str(e)}")
            return False
    
    @staticmethod
    def retry_failed_notifications():
        """
        Retenter d'envoyer les notifications échouées
        """
        failed_notifications = HistoriqueNotifications.objects.filter(
            status='FAILED',
            retry_count__lt=settings.NOTIFICATION_MAX_RETRIES
        )
        
        retry_count = 0
        for notification in failed_notifications:
            success = NotificationManager._send_email(
                recipient_email=notification.recipient_email,
                subject=notification.subject,
                message_text=notification.message_text,
                message_html=notification.message_html,
                notification_id=notification.id
            )
            
            if success:
                notification.status = 'SENT'
                notification.sent_at = datetime.now()
                logger.info(f"[OK] Notification #{notification.id} renvoyee avec succes")
                retry_count += 1
            else:
                notification.retry_count += 1
                logger.warning(f"[FAIL] Tentative #{notification.retry_count} echouee pour notification #{notification.id}")
            
            notification.save()
        
        logger.info(f"Retry notifications: {retry_count} succès sur {len(failed_notifications)} tentatives")
        return retry_count


class NotificationChecker:
    """Vérificateur de quitus expirant bientôt"""
    
    @staticmethod
    def check_expiring_quitus(days_before=None):
        """
        Vérifier et envoyer des notifications pour quitus expirant bientôt
        
        Args:
            days_before: Nombre de jours avant expiration (default: NOTIFICATION_DAYS_BEFORE_EXPIRY)
        
        Returns:
            dict: {'checked': nombre vérifié, 'notified': nombre notifiés, 'errors': nombre d'erreurs}
        """
        if days_before is None:
            days_before = settings.NOTIFICATION_DAYS_BEFORE_EXPIRY
        
        # Calculer la plage de dates
        today = datetime.now().date()
        target_date = today + timedelta(days=days_before)
        
        # Trouver les quitus valides expirant exactement dans 'days_before' jours
        expiring_quitus = Quitus.objects.filter(
            date_validite=target_date,
            statut='ACTIF'  # Le modèle utilise ACTIF pour les quitus valides
        ).select_related('created_by')
        
        checked = expiring_quitus.count()
        notified = 0
        errors = 0
        
        logger.info(f"Verification des quitus expirant le {target_date} - {checked} trouves")
        
        for quitus in expiring_quitus:
            try:
                # Verifier si notification deja envoyee aujourd'hui
                already_notified = HistoriqueNotifications.objects.filter(
                    quitus=quitus,
                    notification_type='EXPIRY_WARNING',
                    created_at__date=today
                ).exists()
                
                if already_notified:
                    logger.info(f"[SKIP] Notification deja envoyee pour {quitus.numero_quitus}")
                    continue
                
                # Determiner destinataire
                recipient_email = quitus.email or (quitus.created_by.email if quitus.created_by else None)
                
                if not recipient_email:
                    logger.warning(f"[WARN] Pas d'email pour {quitus.numero_quitus}")
                    errors += 1
                    continue
                
                # Envoyer notification
                notification = NotificationManager.send_expiry_warning(
                    quitus=quitus,
                    recipient_email=recipient_email,
                    recipient_name=quitus.nom_prenoms
                )
                
                if notification and notification.is_sent:
                    notified += 1
                else:
                    errors += 1
                    
            except Exception as e:
                logger.error(f"Erreur lors du traitement de {quitus.numero_quitus}: {str(e)}")
                errors += 1
        
        result = {'checked': checked, 'notified': notified, 'errors': errors}
        logger.info(f"Verification terminee: {result}")
        return result

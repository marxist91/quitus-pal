from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


class UserProfile(models.Model):
    """Profil utilisateur étendu pour les informations métier"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    matricule = models.CharField(max_length=50, unique=True, verbose_name="Matricule")
    fonction = models.CharField(max_length=100, default="Agent", verbose_name="Fonction")
    telephone = models.CharField(max_length=20, default="+228 00 00 00 00", verbose_name="Téléphone")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'Profil Utilisateur'
        verbose_name_plural = 'Profils Utilisateurs'
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.fonction}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Créer automatiquement un profil quand un utilisateur est créé"""
    if created:
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={
                'matricule': f'USR-{instance.id}',
                'fonction': 'Agent',
                'telephone': '+228 00 00 00 00',
                'actif': True
            }
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarder le profil quand l'utilisateur est sauvegardé"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Quitus(models.Model):
    """Modèle pour les attestations de régularité (Quitus)"""
    
    # Identifiants uniques
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_quitus = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Numéro de Quitus",
        validators=[RegexValidator(
            regex=r'^[A-Z0-9\-]+$',
            message="Format invalide"
        )]
    )
    
    # Dates
    date_creation = models.DateTimeField(auto_now_add=True, null=True, verbose_name="Date de création")
    date_validite = models.DateField(verbose_name="Date de validité")
    date_emission = models.DateField(default=timezone.now, verbose_name="Date d'émission")
    
    # Informations du client
    nom_prenoms = models.CharField(max_length=200, verbose_name="Nom et Prénoms")
    raison_sociale = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="Raison Sociale"
    )
    cni = models.CharField(max_length=50, verbose_name="N° CNI")
    nationalite = models.CharField(max_length=50, default="Togolaise", verbose_name="Nationalité")
    activite = models.CharField(max_length=200, verbose_name="Activité Principale")
    compte_pal = models.CharField(max_length=50, verbose_name="N° Compte PAL")
    nif = models.CharField(max_length=50, verbose_name="NIF")
    
    # Adresse et contact
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(verbose_name="Email")
    situation_geo = models.CharField(max_length=300, verbose_name="Situation Géographique")
    adresse_postale = models.CharField(max_length=200, verbose_name="Adresse Postale")
    
    # Sécurité et validation
    qr_code = models.TextField(blank=True, null=True, verbose_name="Données QR Code")
    qr_code_image = models.ImageField(
        upload_to='qr_codes/', 
        blank=True, 
        null=True, 
        verbose_name="Image QR Code"
    )
    code_verification = models.CharField(
        max_length=100, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name="Code de vérification"
    )
    
    # Utilisateur créateur
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Créé par",
        related_name='quitus_crees',
        null=True,
        blank=True
    )
    
    # Fichier PDF généré
    pdf_file = models.FileField(
        upload_to='quitus_pdf/', 
        blank=True, 
        null=True,
        verbose_name="Fichier PDF"
    )
    
    # Statut
    STATUS_CHOICES = [
        ('ACTIF', 'Actif'),
        ('EXPIRE', 'Expiré'),
        ('ANNULE', 'Annulé'),
    ]
    statut = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ACTIF',
        verbose_name="Statut"
    )
    
    # Métadonnées
    date_modification = models.DateTimeField(auto_now=True)
    ip_creation = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        db_table = 'quitus'
        verbose_name = 'Quitus'
        verbose_name_plural = 'Quitus'
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['numero_quitus']),
            models.Index(fields=['date_creation']),
            models.Index(fields=['statut']),
        ]
    
    def __str__(self):
        return f"{self.numero_quitus} - {self.nom_prenoms}"
    
    def save(self, *args, **kwargs):
        """Surcharge de la méthode save pour générer le code de vérification"""
        if not self.code_verification:
            self.code_verification = self.generer_code_verification()
        
        # Vérifier si le quitus est expiré
        if self.date_validite < timezone.now().date() and self.statut == 'ACTIF':
            self.statut = 'EXPIRE'
        
        super().save(*args, **kwargs)
    
    def generer_code_verification(self):
        """Générer un code de vérification unique"""
        import hashlib
        import time
        data = f"{self.numero_quitus}-{self.nom_prenoms}-{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:20].upper()
    
    @property
    def est_valide(self):
        """Vérifier si le quitus est toujours valide"""
        return self.date_validite >= timezone.now().date() and self.statut == 'ACTIF'
    
    @property
    def jours_restants(self):
        """Calculer le nombre de jours restants avant expiration"""
        if self.est_valide:
            delta = self.date_validite - timezone.now().date()
            return delta.days
        return 0


class HistoriqueQuitus(models.Model):
    """Historique des consultations et modifications de quitus"""
    quitus = models.ForeignKey(Quitus, on_delete=models.CASCADE, related_name='historique', null=True, blank=True)
    action = models.CharField(max_length=50)  # CREATION, CONSULTATION, MODIFICATION, IMPRESSION
    utilisateur = models.CharField(max_length=200, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    date_action = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'historique_quitus'
        verbose_name = 'Historique Quitus'
        verbose_name_plural = 'Historiques Quitus'
        ordering = ['-date_action']
    
    def __str__(self):
        return f"{self.action} - {self.quitus.numero_quitus if self.quitus else 'System'} - {self.date_action}"


class HistoriqueNotifications(models.Model):
    """Historique des notifications envoyées aux utilisateurs"""
    
    NOTIFICATION_TYPES = [
        ('EXPIRY_WARNING', 'Avertissement d\'expiration'),
        ('EXPIRY_EXPIRED', 'Notification d\'expiration'),
        ('VERIFICATION_FAILED', 'Vérification échouée'),
        ('SYSTEM_ALERT', 'Alerte système'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('SENT', 'Envoyé'),
        ('FAILED', 'Échoué'),
        ('BOUNCED', 'Rejeté'),
    ]
    
    quitus = models.ForeignKey(Quitus, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    recipient_email = models.EmailField()
    recipient_name = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    subject = models.CharField(max_length=255)
    message_text = models.TextField()
    message_html = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    retry_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'historique_notifications'
        verbose_name = 'Historique Notification'
        verbose_name_plural = 'Historiques Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['recipient_email', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.recipient_email} - {self.status}"
    
    @property
    def is_pending(self):
        """Vérifier si la notification est en attente"""
        return self.status == 'PENDING'
    
    @property
    def is_sent(self):
        """Vérifier si la notification a été envoyée"""
        return self.status == 'SENT'
    
    @property
    def days_since_created(self):
        """Nombre de jours depuis la création"""
        from datetime import datetime, timezone
        return (datetime.now(timezone.utc) - self.created_at).days



class RenumberBatch(models.Model):
    """Batch de renumérotation sauvegardé pour prévisualisation, export et annulation."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=50)
    params = models.JSONField(blank=True, null=True)
    changes = models.JSONField(blank=True, null=True)  # liste d'objets {id, old, new}
    created_by = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    applied_by = models.CharField(max_length=200, blank=True, null=True)
    result = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'renumber_batch'
        verbose_name = 'Renumber Batch'
        verbose_name_plural = 'Renumber Batches'

    def __str__(self):
        return f"Batch {self.id} - {self.action} - applied={self.applied}"
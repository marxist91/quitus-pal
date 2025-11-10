from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from .models import Quitus
from .pdf_generator import generate_quitus_pdf

# Champs critiques qui déclenchent une régénération du PDF
CRITICAL_FIELDS = {
    'numero_quitus', 'date_validite', 'date_emission', 'nom_prenoms',
    'raison_sociale', 'cni', 'nationalite', 'activite', 'compte_pal',
    'nif', 'telephone', 'email', 'situation_geo', 'adresse_postale'
}

# Cache pour stocker les anciennes valeurs avant mise à jour
_quitus_old_values = {}

@receiver(pre_save, sender=Quitus)
def capture_old_values(sender, instance: Quitus, **kwargs):
    """Capture les anciennes valeurs des champs critiques avant mise à jour."""
    if instance.pk:
        try:
            old = Quitus.objects.get(pk=instance.pk)
            _quitus_old_values[instance.pk] = {
                field: getattr(old, field) for field in CRITICAL_FIELDS
            }
        except Quitus.DoesNotExist:
            pass

@receiver(post_save, sender=Quitus)
def auto_generate_pdf(sender, instance: Quitus, created, **kwargs):
    """Génère et attache automatiquement le PDF après création ou modification de champs critiques."""
    regenerate = created
    
    if not created and instance.pk in _quitus_old_values:
        old_values = _quitus_old_values.pop(instance.pk)
        # Vérifier si un champ critique a changé
        for field in CRITICAL_FIELDS:
            if getattr(instance, field) != old_values.get(field):
                regenerate = True
                break
    
    if regenerate:
        try:
            pdf_buffer = generate_quitus_pdf(instance)
            instance.pdf_file.save(
                f'quitus_{instance.numero_quitus}.pdf',
                ContentFile(pdf_buffer.read()),
                save=False  # Évite la boucle infinie (on ne sauve que le fichier, pas le modèle)
            )
            # Mise à jour du champ sans déclencher post_save à nouveau
            Quitus.objects.filter(pk=instance.pk).update(pdf_file=instance.pdf_file.name)
        except Exception:
            # On ignore silencieusement pour ne pas bloquer la sauvegarde
            pass

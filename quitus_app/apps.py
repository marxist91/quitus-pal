from django.apps import AppConfig


class QuitusAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quitus_app'
    verbose_name = 'Gestion des Quitus'

    def ready(self):
        # Import des signaux pour génération/attachement auto du PDF
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Évite de faire échouer le démarrage si la BD n'est pas prête
            pass

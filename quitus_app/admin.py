from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Agent, Quitus, HistoriqueQuitus


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['nom_complet', 'matricule', 'fonction', 'email', 'actif', 'date_creation']
    list_filter = ['actif', 'fonction', 'date_creation']
    search_fields = ['nom_complet', 'matricule', 'email']
    ordering = ['nom_complet']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom_complet', 'matricule', 'fonction')
        }),
        ('Contact', {
            'fields': ('email', 'telephone')
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
    )
    
    readonly_fields = ['date_creation', 'date_modification']


class HistoriqueQuituslInline(admin.TabularInline):
    model = HistoriqueQuitus
    extra = 0
    readonly_fields = ['action', 'utilisateur', 'ip_address', 'date_action', 'details']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Quitus)
class QuitusAdmin(admin.ModelAdmin):
    list_display = [
        'numero_quitus',
        'nom_prenoms',
        'date_validite',
        'statut_badge',
        'agent',
        'date_creation',
        'actions_links'
    ]
    list_filter = ['statut', 'date_creation', 'date_validite', 'agent']
    search_fields = [
        'numero_quitus',
        'nom_prenoms',
        'raison_sociale',
        'cni',
        'email',
        'telephone'
    ]
    ordering = ['-date_creation']
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        ('Identification', {
            'fields': ('numero_quitus', 'date_validite', 'date_emission', 'statut')
        }),
        ('Client', {
            'fields': (
                'nom_prenoms',
                'raison_sociale',
                'cni',
                'nationalite',
                'activite',
                'compte_pal',
                'nif'
            )
        }),
        ('Contact', {
            'fields': ('telephone', 'email', 'situation_geo', 'adresse_postale')
        }),
        ('Sécurité', {
            'fields': ('code_verification', 'qr_code', 'qr_code_image'),
            'classes': ('collapse',)
        }),
        ('Agent et fichiers', {
            'fields': ('agent', 'pdf_file')
        }),
        ('Métadonnées', {
            'fields': ('ip_creation', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'code_verification',
        'qr_code',
        'date_creation',
        'date_modification',
        'ip_creation'
    ]
    
    inlines = [HistoriqueQuituslInline]
    
    def statut_badge(self, obj):
        """Afficher le statut avec une badge colorée"""
        colors = {
            'ACTIF': 'success',
            'EXPIRE': 'warning',
            'ANNULE': 'danger'
        }
        color = colors.get(obj.statut, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'
    
    def actions_links(self, obj):
        """Liens d'actions rapides"""
        telecharger_url = reverse('quitus:telecharger', args=[obj.numero_quitus])
        verifier_url = reverse('quitus:verifier', args=[obj.code_verification])
        
        return format_html(
            '<a class="button" href="{}" target="_blank">📥 PDF</a> '
            '<a class="button" href="{}" target="_blank">🔍 Vérifier</a>',
            telecharger_url,
            verifier_url
        )
    actions_links.short_description = 'Actions'
    
    def get_readonly_fields(self, request, obj=None):
        """Rendre certains champs non modifiables après création"""
        if obj:  # Si l'objet existe déjà
            return self.readonly_fields + ['numero_quitus']
        return self.readonly_fields
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


@admin.register(HistoriqueQuitus)
class HistoriqueQuitusAdmin(admin.ModelAdmin):
    list_display = ['quitus', 'action', 'utilisateur', 'ip_address', 'date_action']
    list_filter = ['action', 'date_action']
    search_fields = ['quitus__numero_quitus', 'utilisateur', 'ip_address']
    ordering = ['-date_action']
    date_hierarchy = 'date_action'
    
    readonly_fields = ['quitus', 'action', 'utilisateur', 'ip_address', 'date_action', 'details']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
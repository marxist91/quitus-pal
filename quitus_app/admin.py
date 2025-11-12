from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import UserProfile, Quitus, HistoriqueQuitus


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'matricule', 'fonction', 'telephone', 'actif', 'date_creation']
    list_filter = ['actif', 'fonction', 'date_creation']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'matricule']
    ordering = ['user__last_name', 'user__first_name']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Informations professionnelles', {
            'fields': ('matricule', 'fonction')
        }),
        ('Contact', {
            'fields': ('telephone',)
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
        'created_by',
        'date_creation',
        'actions_links'
    ]
    list_filter = ['statut', 'date_creation', 'date_validite', 'created_by']
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
        ('Créateur et fichiers', {
            'fields': ('created_by', 'pdf_file')
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
        if obj.pdf_file:
            telecharger_url = reverse('telecharger_quitus', args=[obj.numero_quitus])
            pdf_link = f'<a class="button" href="{telecharger_url}" target="_blank">📥 PDF</a> '
        else:
            pdf_link = '<span style="color: #999;">📥 Pas de PDF</span> '
        
        verifier_url = reverse('verifier_quitus', args=[obj.code_verification])
        
        return format_html(
            '{}<a class="button" href="{}" target="_blank">🔍 Vérifier</a>',
            pdf_link,
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
# quitus_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('history/', views.history_log, name='history_log'),
    
    # Administration des utilisateurs
    path('dashboard/users/', views.dashboard_users, name='dashboard_users'),
    path('dashboard/users/add/', views.add_user, name='add_user'),
    path('dashboard/users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('dashboard/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('dashboard/users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    
    # Navigation
    path('', views.index, name='index'),
    path('creer/', views.creer_quitus, name='creer_quitus'),
    path('api/client-by-compte/', views.client_by_compte, name='client_by_compte'),
    path('verification/', views.verification_page, name='verification_page'),
    path('quitus/<str:numero_quitus>/', views.detail_quitus, name='detail_quitus'),
    path('telecharger/<str:numero_quitus>/', views.telecharger_quitus, name='telecharger_quitus'),
    path('verifier/<str:code_verification>/', views.verifier_quitus, name='verifier_quitus'),
    path('liste/', views.liste_quitus, name='liste_quitus'),
    path('recherche/', views.recherche_quitus, name='recherche_quitus'),
    path('export-csv/', views.export_quitus_csv, name='export_quitus_csv'),
    path('export-excel/', views.export_quitus_excel, name='export_quitus_excel'),
    path('export-history-excel/', views.export_history_excel, name='export_history_excel'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('dashboard/regen-numeros/', views.admin_regenerate_numeros, name='admin_regenerate_numeros'),
    path('dashboard/regen-numeros/export/', views.admin_regenerate_export_csv, name='admin_regenerate_export_csv'),
    path('dashboard/regen-numeros/undo/<str:batch_id>/', views.admin_regenerate_undo, name='admin_regenerate_undo'),
    path('dashboard/regen-batches/', views.admin_list_batches, name='admin_list_renumber_batches'),
    path('dashboard/regen-batches/<str:batch_id>/', views.admin_preview_batch, name='admin_preview_renumber_batch'),
    path('notifications/', views.notifications_dashboard, name='notifications_dashboard'),
    path('notifications/<int:notification_id>/retry/', views.retry_notification, name='retry_notification'),
    path('notifications/retry-all/', views.retry_all_failed_notifications, name='retry_all_failed_notifications'),
    path('expiry-monitor/', views.expiry_monitor, name='expiry_monitor'),
    path('expiry-monitor/<uuid:quitus_id>/send/', views.send_expiry_notification, name='send_expiry_notification'),
    path('expiry-monitor/send-all/', views.send_all_expiry_notifications, name='send_all_expiry_notifications'),
    path('quitus/<uuid:quitus_id>/edit/', views.edit_quitus, name='edit_quitus'),
    path('quitus/<uuid:quitus_id>/cancel/', views.cancel_quitus, name='cancel_quitus'),
]


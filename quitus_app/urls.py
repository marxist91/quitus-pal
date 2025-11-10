# quitus_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Administration
    path('admin/roles/', views.manage_user_roles, name='manage_user_roles'),
    
    # Navigation
    path('', views.index, name='index'),
    path('creer/', views.creer_quitus, name='creer_quitus'),
    path('verification/', views.verification_page, name='verification_page'),
    path('quitus/<str:numero_quitus>/', views.detail_quitus, name='detail_quitus'),
    path('telecharger/<str:numero_quitus>/', views.telecharger_quitus, name='telecharger_quitus'),
    path('verifier/<str:code_verification>/', views.verifier_quitus, name='verifier_quitus'),
    path('liste/', views.liste_quitus, name='liste_quitus'),
    path('recherche/', views.recherche_quitus, name='recherche_quitus'),
    path('export-csv/', views.export_quitus_csv, name='export_quitus_csv'),
]

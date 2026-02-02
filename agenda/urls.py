from django.urls import path
from . import views

app_name = 'agenda'

urlpatterns = [
    # Vue principale
    path('<str:institut_code>/', views.index, name='index'),

    # Clôture de caisse
    path('<str:institut_code>/cloture/', views.cloture_caisse, name='cloture_caisse'),
    path('<str:institut_code>/api/cloture/', views.api_cloturer_caisse, name='api_cloturer_caisse'),

    # API
    path('<str:institut_code>/api/prestations/', views.api_prestations, name='api_prestations'),
    path('<str:institut_code>/api/rdv/creer/', views.api_rdv_creer, name='api_rdv_creer'),
    path('<str:institut_code>/api/rdv/<int:rdv_id>/', views.api_rdv_details, name='api_rdv_details'),
    path('<str:institut_code>/api/rdv/<int:rdv_id>/modifier/', views.api_rdv_modifier, name='api_rdv_modifier'),
    path('<str:institut_code>/api/rdv/<int:rdv_id>/supprimer/', views.api_rdv_supprimer, name='api_rdv_supprimer'),
    path('<str:institut_code>/api/rdv/<int:rdv_id>/deplacer/', views.api_rdv_deplacer, name='api_rdv_deplacer'),
    path('<str:institut_code>/api/rdv/<int:rdv_id>/annuler/', views.api_rdv_annuler, name='api_rdv_annuler'),
    path('<str:institut_code>/api/rdv/<int:rdv_id>/absent/', views.api_rdv_absent, name='api_rdv_absent'),
    path('<str:institut_code>/api/rdv/<int:rdv_id>/annule-client/', views.api_rdv_annule_client, name='api_rdv_annule_client'),
    path('<str:institut_code>/api/rdv/<int:rdv_id>/valider/', views.api_rdv_valider, name='api_rdv_valider'),

    # Forfaits multi-séances
    path('<str:institut_code>/api/forfaits/', views.api_forfaits_disponibles, name='api_forfaits_disponibles'),
    path('<str:institut_code>/api/forfaits/client/<int:client_id>/', views.api_forfaits_client, name='api_forfaits_client'),
    path('<str:institut_code>/api/forfaits/acheter/', views.api_forfait_acheter, name='api_forfait_acheter'),
    path('<str:institut_code>/api/forfaits/<int:forfait_id>/supprimer/', views.api_forfait_supprimer, name='api_forfait_supprimer'),
]

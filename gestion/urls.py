from django.urls import path
from . import views

app_name = 'gestion'

urlpatterns = [
    # Catalogue - Vue principale
    path('catalogue/', views.catalogue_view, name='catalogue'),

    # Familles
    path('catalogue/famille/creer/', views.creer_famille, name='creer_famille'),
    path('catalogue/famille/<int:famille_id>/modifier/', views.modifier_famille, name='modifier_famille'),
    path('catalogue/famille/<int:famille_id>/supprimer/', views.supprimer_famille, name='supprimer_famille'),
    path('catalogue/famille/<int:famille_id>/info-suppression/', views.famille_info_suppression, name='famille_info_suppression'),
    path('catalogue/famille/<int:famille_id>/deplacer/<str:direction>/', views.deplacer_famille, name='deplacer_famille'),

    # Prestations
    path('catalogue/prestation/creer/', views.creer_prestation, name='creer_prestation'),
    path('catalogue/prestation/<int:prestation_id>/modifier/', views.modifier_prestation, name='modifier_prestation'),
    path('catalogue/prestation/<int:prestation_id>/supprimer/', views.supprimer_prestation, name='supprimer_prestation'),
    path('catalogue/prestation/<int:prestation_id>/info-suppression/', views.prestation_info_suppression, name='prestation_info_suppression'),
    path('catalogue/prestation/<int:prestation_id>/details/', views.prestation_details, name='prestation_details'),
    path('catalogue/prestation/<int:prestation_id>/toggle-actif/', views.toggle_prestation_actif, name='toggle_prestation_actif'),
    path('catalogue/prestation/<int:prestation_id>/deplacer/<str:direction>/', views.deplacer_prestation, name='deplacer_prestation'),

    # Réordonnancement drag & drop
    path('catalogue/institut/<int:institut_id>/reordonner-familles/', views.reordonner_familles, name='reordonner_familles'),
    path('catalogue/famille/<int:famille_id>/reordonner-prestations/', views.reordonner_prestations, name='reordonner_prestations'),

    # Export Excel
    path('catalogue/export-excel/', views.export_catalogue_excel, name='export_catalogue_excel'),
]

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

    # Options
    path('catalogue/<str:institut_code>/options/', views.api_options_liste, name='api_options_liste'),
    path('catalogue/<str:institut_code>/option/creer/', views.api_option_creer, name='api_option_creer'),
    path('catalogue/<str:institut_code>/option/<int:option_id>/modifier/', views.api_option_modifier, name='api_option_modifier'),
    path('catalogue/<str:institut_code>/option/<int:option_id>/supprimer/', views.api_option_supprimer, name='api_option_supprimer'),
    path('catalogue/<str:institut_code>/option/<int:option_id>/details/', views.api_option_details, name='api_option_details'),

    # ========== PRÉSENCES ==========
    path('presences/', views.presences_pointage, name='presences_pointage'),
    path('presences/historique/', views.presences_historique, name='presences_historique'),
    path('presences/absences/', views.absences_liste, name='absences_liste'),
    path('presences/retards/', views.retards_suivi, name='retards_suivi'),
    path('presences/api/pointer/', views.api_pointer, name='api_pointer'),
    path('presences/api/absence/creer/', views.api_absence_creer, name='api_absence_creer'),
    path('presences/api/absence/<int:absence_id>/supprimer/', views.api_absence_supprimer, name='api_absence_supprimer'),
    path('presences/api/avertissement/creer/', views.api_avertissement_creer, name='api_avertissement_creer'),

    # ========== SALAIRES ==========
    path('salaires/', views.salaires_calcul, name='salaires_calcul'),
    path('salaires/primes/', views.primes_liste, name='primes_liste'),
    path('salaires/avances/', views.avances_liste, name='avances_liste'),
    path('salaires/api/calculer/', views.api_calculer_salaire, name='api_calculer_salaire'),
    path('salaires/api/valider/<int:calcul_id>/', views.api_valider_salaire, name='api_valider_salaire'),
    path('salaires/api/prime/creer/', views.api_prime_creer, name='api_prime_creer'),
    path('salaires/api/prime/<int:prime_id>/supprimer/', views.api_prime_supprimer, name='api_prime_supprimer'),
    path('salaires/api/avance/creer/', views.api_avance_creer, name='api_avance_creer'),
    path('salaires/api/avance/<int:avance_id>/supprimer/', views.api_avance_supprimer, name='api_avance_supprimer'),

    # ========== STOCKS ==========
    path('stocks/', views.stocks_produits, name='stocks_produits'),
    path('stocks/mouvements/', views.stocks_mouvements, name='stocks_mouvements'),
    path('stocks/api/produit/creer/', views.api_produit_creer, name='api_produit_creer'),
    path('stocks/api/produit/<int:produit_id>/modifier/', views.api_produit_modifier, name='api_produit_modifier'),
    path('stocks/api/produit/<int:produit_id>/supprimer/', views.api_produit_supprimer, name='api_produit_supprimer'),
    path('stocks/api/mouvement/creer/', views.api_mouvement_creer, name='api_mouvement_creer'),
    path('stocks/parametres/', views.stocks_parametres, name='stocks_parametres'),
    path('stocks/api/categorie/creer/', views.api_categorie_produit_creer, name='api_categorie_produit_creer'),
    path('stocks/api/categorie/<int:pk>/modifier/', views.api_categorie_produit_modifier, name='api_categorie_produit_modifier'),
    path('stocks/api/categorie/<int:pk>/supprimer/', views.api_categorie_produit_supprimer, name='api_categorie_produit_supprimer'),
    path('stocks/api/unite/creer/', views.api_unite_creer, name='api_unite_creer'),
    path('stocks/api/unite/<int:pk>/modifier/', views.api_unite_modifier, name='api_unite_modifier'),
    path('stocks/api/unite/<int:pk>/supprimer/', views.api_unite_supprimer, name='api_unite_supprimer'),
    path('stocks/api/fournisseur/creer/', views.api_fournisseur_creer, name='api_fournisseur_creer'),
    path('stocks/api/fournisseur/<int:pk>/modifier/', views.api_fournisseur_modifier, name='api_fournisseur_modifier'),
    path('stocks/api/fournisseur/<int:pk>/supprimer/', views.api_fournisseur_supprimer, name='api_fournisseur_supprimer'),

    # ========== STOCKS — INVENTAIRE ==========
    path('stocks/inventaire/', views.inventaire_liste, name='inventaire_liste'),
    path('stocks/inventaire/nouveau/', views.inventaire_nouveau, name='inventaire_nouveau'),
    path('stocks/inventaire/<int:inventaire_id>/', views.inventaire_detail, name='inventaire_detail'),
    path('stocks/inventaire/<int:inventaire_id>/cloturer/', views.api_inventaire_cloturer, name='api_inventaire_cloturer'),
    path('stocks/inventaire/<int:inventaire_id>/ligne/<int:ligne_id>/saisir/', views.api_inventaire_saisir, name='api_inventaire_saisir'),

    # ========== DÉPENSES ==========
    path('depenses/', views.depenses_liste, name='depenses_liste'),
    path('depenses/api/creer/', views.api_depense_creer, name='api_depense_creer'),
    path('depenses/api/<int:depense_id>/supprimer/', views.api_depense_supprimer, name='api_depense_supprimer'),
    path('depenses/api/categorie/creer/', views.api_categorie_depense_creer, name='api_categorie_depense_creer'),
    path('depenses/api/categorie/<int:pk>/supprimer/', views.api_categorie_depense_supprimer, name='api_categorie_depense_supprimer'),

    # ========== DÉPENSES RÉCURRENTES ==========
    path('depenses/recurrentes/', views.depenses_recurrentes, name='depenses_recurrentes'),
    path('depenses/recurrentes/api/creer/', views.api_depense_recurrente_creer, name='api_depense_recurrente_creer'),
    path('depenses/recurrentes/api/<int:dr_id>/modifier/', views.api_depense_recurrente_modifier, name='api_depense_recurrente_modifier'),
    path('depenses/recurrentes/api/<int:dr_id>/supprimer/', views.api_depense_recurrente_supprimer, name='api_depense_recurrente_supprimer'),
    path('depenses/recurrentes/api/validation/<int:val_id>/valider/', views.api_validation_valider, name='api_validation_valider'),
    path('depenses/recurrentes/api/validation/<int:val_id>/ignorer/', views.api_validation_ignorer, name='api_validation_ignorer'),

    # ========== BILAN ==========
    path('bilan/', views.bilan_mensuel, name='bilan_mensuel'),

    # ========== VENTES PRODUITS ==========
    path('ventes/', views.ventes_caisse, name='ventes_caisse'),
    path('ventes/historique/', views.ventes_historique, name='ventes_historique'),
    path('ventes/api/vendre/', views.api_vendre, name='api_vendre'),

    # ========== RÉCONCILIATION ==========
    path('reconciliation/', views.reconciliation_index, name='reconciliation_index'),
    path('reconciliation/api/calculer/', views.api_reconciliation_calculer, name='api_reconciliation_calculer'),
    path('reconciliation/api/valider/', views.api_reconciliation_valider, name='api_reconciliation_valider'),
]

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Clients
    path('clients/', views.clients_list, name='clients_list'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('clients/nouveau/', views.client_create, name='client_create'),
    path('api/clients/search/', views.client_search, name='client_search'),
    path('api/clients/creer/', views.api_client_creer, name='api_client_creer'),
    path('api/clients/<int:pk>/modifier/', views.api_client_modifier, name='api_client_modifier'),
    path('api/clients/<int:pk>/supprimer/', views.api_client_supprimer, name='api_client_supprimer'),
    path('api/clients/<int:pk>/desactiver/', views.api_client_desactiver, name='api_client_desactiver'),

    # Employés (patron uniquement)
    path('employes/', views.employes_list, name='employes_list'),
    path('api/employes/creer/', views.api_employe_creer, name='api_employe_creer'),
    path('api/employes/<int:pk>/modifier/', views.api_employe_modifier, name='api_employe_modifier'),
    path('api/employes/<int:pk>/supprimer/', views.api_employe_supprimer, name='api_employe_supprimer'),

    # Cartes cadeaux
    path('cartes-cadeaux/', views.cartes_cadeaux_list, name='cartes_cadeaux_list'),
    path('cartes-cadeaux/<int:carte_id>/imprimer/', views.imprimer_carte_cadeau, name='imprimer_carte_cadeau'),
    path('api/cartes-cadeaux/vendre/', views.api_vendre_carte_cadeau, name='api_vendre_carte_cadeau'),
    path('api/cartes-cadeaux/verifier/', views.api_verifier_carte_cadeau, name='api_verifier_carte_cadeau'),
    path('api/cartes-cadeaux/client/', views.api_rechercher_cartes_client, name='api_rechercher_cartes_client'),
    path('api/cartes-cadeaux/<int:carte_id>/supprimer/', views.api_supprimer_carte_cadeau, name='api_supprimer_carte_cadeau'),
    path('api/cartes-cadeaux/<int:carte_id>/whatsapp/<str:destinataire>/', views.api_carte_cadeau_whatsapp, name='api_carte_cadeau_whatsapp'),
]

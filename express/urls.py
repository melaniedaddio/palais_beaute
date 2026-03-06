from django.urls import path
from . import views

app_name = 'express'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/vente/creer/', views.creer_vente, name='creer_vente'),
    path('cloture/', views.cloture_caisse, name='cloture_caisse'),
    path('api/cloture/', views.api_cloturer_caisse, name='api_cloturer_caisse'),
    path('historique/', views.historique, name='historique'),
]

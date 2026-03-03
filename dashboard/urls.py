from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('depenses/', views.dashboard_depenses, name='depenses'),
    path('bilan/', views.dashboard_bilan, name='bilan'),
    path('api/stats/', views.api_stats_chart, name='api_stats'),
    path('api/stats/institut/', views.api_stats_institut, name='api_stats_institut'),
    path('export/rdv/', views.export_rdv_excel, name='export_rdv'),
]

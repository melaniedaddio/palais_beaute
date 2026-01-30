from django.urls import path
from . import views

app_name = 'credits'

urlpatterns = [
    path('<str:institut_code>/', views.index, name='index'),
    path('<str:institut_code>/client/<int:client_id>/', views.client_detail, name='client_detail'),
    path('<str:institut_code>/api/credit/<int:credit_id>/', views.api_credit_details, name='api_credit_details'),
    path('<str:institut_code>/api/credit/<int:credit_id>/regler/', views.regler_credit, name='regler_credit'),
]

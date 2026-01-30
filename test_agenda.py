"""
Script de test pour créer des données de test pour l'agenda
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'le_palais_beaute.settings')
django.setup()

from core.models import Institut, Client, Employe, RendezVous, Prestation, Utilisateur
from django.contrib.auth import get_user_model
from datetime import date, time

User = get_user_model()

# Récupérer l'institut Le Palais
palais = Institut.objects.get(code='palais')

# Récupérer le patron (Utilisateur, pas User)
patron_user = User.objects.get(username='patron')
patron = patron_user.utilisateur

# Créer des clients de test
clients_data = [
    {'prenom': 'Aminata', 'nom': 'Koné', 'telephone': '0707070701'},
    {'prenom': 'Fatou', 'nom': 'Diallo', 'telephone': '0707070702'},
    {'prenom': 'Mariam', 'nom': 'Traoré', 'telephone': '0707070703'},
    {'prenom': 'Aïcha', 'nom': 'Sanogo', 'telephone': '0707070704'},
    {'prenom': 'Kadiatou', 'nom': 'Coulibaly', 'telephone': '0707070705'},
]

print("\n[OK] Création des clients de test...")
for client_data in clients_data:
    client, created = Client.objects.get_or_create(
        telephone=client_data['telephone'],
        defaults=client_data
    )
    if created:
        print(f"  - {client.prenom} {client.nom} créé(e)")
    else:
        print(f"  - {client.prenom} {client.nom} existe déjà")

# Récupérer des employés de Le Palais
employes = Employe.objects.filter(institut=palais, actif=True)[:3]
print(f"\n[OK] {employes.count()} employés trouvés pour Le Palais")

# Récupérer des prestations
prestations = Prestation.objects.filter(famille__institut=palais, actif=True)[:5]
print(f"[OK] {prestations.count()} prestations trouvées")

# Créer quelques RDV de test pour aujourd'hui
print("\n[OK] Création de rendez-vous de test...")
rdv_data = [
    {'employe': employes[0], 'client': Client.objects.get(telephone='0707070701'), 'prestation': prestations[0], 'heure': time(9, 0)},
    {'employe': employes[0], 'client': Client.objects.get(telephone='0707070702'), 'prestation': prestations[1], 'heure': time(11, 0)},
    {'employe': employes[1], 'client': Client.objects.get(telephone='0707070703'), 'prestation': prestations[2], 'heure': time(10, 0)},
    {'employe': employes[1], 'client': Client.objects.get(telephone='0707070704'), 'prestation': prestations[3], 'heure': time(14, 0)},
]

if len(employes) > 2:
    rdv_data.append({'employe': employes[2], 'client': Client.objects.get(telephone='0707070705'), 'prestation': prestations[4], 'heure': time(15, 30)})

for rdv in rdv_data:
    rdv_obj, created = RendezVous.objects.get_or_create(
        institut=palais,
        employe=rdv['employe'],
        client=rdv['client'],
        date=date.today(),
        heure_debut=rdv['heure'],
        defaults={
            'prestation': rdv['prestation'],
            'famille': rdv['prestation'].famille,
            'prix_base': rdv['prestation'].prix,
            'prix_options': 0,
            'statut': 'planifie',
            'cree_par': patron
        }
    )
    if created:
        print(f"  - RDV créé : {rdv['client'].prenom} {rdv['client'].nom} avec {rdv['employe'].nom} à {rdv['heure']}")
    else:
        print(f"  - RDV existe déjà : {rdv['client'].prenom} {rdv['client'].nom} avec {rdv['employe'].nom} à {rdv['heure']}")

print("\n[SUCCES] Données de test créées avec succès!")
print(f"\nPour tester l'agenda :")
print(f"1. Ouvrir http://localhost:8000/")
print(f"2. Se connecter avec le Patron (PIN: 123456)")
print(f"3. Cliquer sur 'Agenda Le Palais'")
print(f"4. Vous devriez voir {len(rdv_data)} RDV sur la grille")

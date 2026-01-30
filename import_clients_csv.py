"""
Script pour importer les clients depuis le fichier CSV
"""
import os
import django
import csv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'le_palais_beaute.settings')
django.setup()

from core.models import Client

# Lire le fichier CSV
csv_file = 'contacts.csv'

print(f"[INFO] Lecture du fichier {csv_file}...")

clients_crees = 0
clients_existants = 0
erreurs = 0

with open(csv_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')

    for row in reader:
        try:
            nom_complet = row['Nom_Complet'].strip()
            telephone = row['Telephone'].strip()

            # Nettoyer le téléphone (enlever les espaces et caractères spéciaux)
            # Garder seulement le premier numéro si plusieurs sont séparés par ;
            if ';' in telephone:
                telephone = telephone.split(';')[0].strip()

            # Remplacer les formats scientifiques
            if 'E+' in telephone:
                # C'est un format scientifique, le convertir
                try:
                    telephone = str(int(float(telephone)))
                except:
                    print(f"  [WARN] Téléphone invalide pour {nom_complet}: {telephone}")
                    continue

            # Nettoyer les espaces
            telephone = telephone.replace(' ', '')

            # Extraire prénom et nom
            parts = nom_complet.split(' ', 1)
            if len(parts) == 2:
                prenom = parts[0].strip()
                nom = parts[1].strip()
            else:
                prenom = parts[0].strip()
                nom = ''

            # Vérifier si le client existe déjà
            if Client.objects.filter(telephone=telephone).exists():
                clients_existants += 1
                continue

            # Créer le client
            Client.objects.create(
                prenom=prenom,
                nom=nom,
                telephone=telephone,
                sexe='F'  # Par défaut femme pour un institut de beauté
            )
            clients_crees += 1

            if clients_crees % 50 == 0:
                print(f"  [INFO] {clients_crees} clients créés...")

        except Exception as e:
            erreurs += 1
            print(f"  [ERREUR] Ligne {nom_complet}: {str(e)}")

print(f"\n[SUCCES] Import terminé !")
print(f"  - Clients créés: {clients_crees}")
print(f"  - Clients déjà existants: {clients_existants}")
print(f"  - Erreurs: {erreurs}")
print(f"  - Total: {clients_crees + clients_existants + erreurs}")

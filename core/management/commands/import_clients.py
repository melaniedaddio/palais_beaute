import csv
import re
from django.core.management.base import BaseCommand
from core.models import Client


class Command(BaseCommand):
    help = 'Importe les clients depuis un fichier CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Chemin vers le fichier CSV')
        parser.add_argument('--dry-run', action='store_true', help='Affiche ce qui serait importé sans créer')

    def clean_phone(self, phone_str):
        """Nettoie et formate le numéro de téléphone"""
        if not phone_str:
            return None
            
        phone_str = str(phone_str).strip()
        
        # Prendre le premier numéro si plusieurs
        if ';' in phone_str:
            phone_str = phone_str.split(';')[0].strip()
        
        # Gérer la notation scientifique (ex: 2,25071E+12)
        if 'E+' in phone_str.upper() or 'e+' in phone_str:
            try:
                # Remplacer la virgule par un point
                phone_str = phone_str.replace(',', '.')
                number = float(phone_str)
                phone_str = str(int(number))
            except:
                pass
        
        # Supprimer les espaces et caractères non numériques (sauf +)
        phone_str = re.sub(r'[^\d+]', '', phone_str)
        
        # Formater pour la Côte d'Ivoire
        # Si commence par +225, garder tel quel
        # Si commence par 225, ajouter +
        # Si commence par 0 et a 10 chiffres, c'est un numéro local
        
        if phone_str.startswith('+'):
            return phone_str
        elif phone_str.startswith('225') and len(phone_str) >= 12:
            return phone_str  # Garder sans +
        elif phone_str.startswith('0') and len(phone_str) == 10:
            return phone_str
        elif phone_str.startswith('33') and len(phone_str) >= 11:
            return phone_str  # Numéro français
        
        return phone_str if phone_str else None

    def split_name(self, full_name):
        """Sépare le nom complet en nom et prénom"""
        full_name = full_name.strip()
        parts = full_name.split()
        
        if len(parts) == 0:
            return '', ''
        elif len(parts) == 1:
            return parts[0], ''
        else:
            # Le premier mot est le nom, le reste est le prénom
            nom = parts[0]
            prenom = ' '.join(parts[1:])
            return nom, prenom

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        
        self.stdout.write(f"Lecture du fichier: {csv_file}")
        
        created = 0
        skipped = 0
        errors = []
        
        # Détecter l'encodage et le délimiteur
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            # Lire la première ligne pour détecter le délimiteur
            first_line = f.readline()
            delimiter = ';' if ';' in first_line else ','
            f.seek(0)
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for row in reader:
                try:
                    # Récupérer les valeurs
                    full_name = row.get('Nom_Complet', '') or row.get('nom_complet', '')
                    telephone = row.get('Telephone', '') or row.get('telephone', '')
                    
                    if not full_name or not telephone:
                        errors.append(f"Ligne ignorée (données manquantes): {row}")
                        skipped += 1
                        continue
                    
                    # Nettoyer le téléphone
                    telephone = self.clean_phone(telephone)
                    
                    if not telephone or len(telephone) < 8:
                        errors.append(f"Téléphone invalide pour {full_name}: {row.get('Telephone', '')}")
                        skipped += 1
                        continue
                    
                    # Séparer nom et prénom
                    nom, prenom = self.split_name(full_name)
                    
                    if not nom:
                        errors.append(f"Nom invalide: {full_name}")
                        skipped += 1
                        continue
                    
                    # Vérifier si le client existe déjà
                    if Client.objects.filter(telephone=telephone).exists():
                        self.stdout.write(f"  - {full_name} ({telephone}) existe déjà")
                        skipped += 1
                        continue
                    
                    if dry_run:
                        self.stdout.write(f"  [DRY-RUN] Créerait: {nom} {prenom} ({telephone})")
                    else:
                        Client.objects.create(
                            nom=nom,
                            prenom=prenom,
                            telephone=telephone,
                            sexe='F'  # Par défaut femme
                        )
                        self.stdout.write(f"  + Créé: {nom} {prenom} ({telephone})")
                    
                    created += 1
                    
                except Exception as e:
                    errors.append(f"Erreur pour {row}: {str(e)}")
                    skipped += 1
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"Résumé:")
        self.stdout.write(f"  - Clients créés: {created}")
        self.stdout.write(f"  - Ignorés/erreurs: {skipped}")
        
        if errors and len(errors) <= 20:
            self.stdout.write("\nErreurs:")
            for err in errors:
                self.stdout.write(f"  {err}")
        elif errors:
            self.stdout.write(f"\n{len(errors)} erreurs (affichage des 10 premières):")
            for err in errors[:10]:
                self.stdout.write(f"  {err}")

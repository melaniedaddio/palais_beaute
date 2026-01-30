"""
Management command to update prestations from CSV file.
"""
import csv
import re
from decimal import Decimal
from django.core.management.base import BaseCommand
from core.models import Institut, FamillePrestation, Prestation, Option


class Command(BaseCommand):
    help = 'Met à jour les prestations depuis le fichier CSV de référence'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            default='catalogue_prestations_complet.csv',
            help='Chemin vers le fichier CSV'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Afficher les modifications sans les appliquer'
        )

    def parse_duree(self, duree_str):
        """Convertit une durée texte en décimal (heures)"""
        if not duree_str or duree_str.strip() == '':
            return Decimal('1.0')  # Défaut 1h pour les options

        duree_str = duree_str.strip().lower()

        # Formats: "1h", "30 min", "1h30", "45 min", "2h", "1h30"
        if 'h' in duree_str and 'min' in duree_str:
            # Ex: "1h30 min" -> 1.5
            match = re.match(r'(\d+)h\s*(\d+)', duree_str)
            if match:
                heures = int(match.group(1))
                minutes = int(match.group(2))
                return Decimal(str(heures + minutes / 60))
        elif 'h' in duree_str:
            # Ex: "1h", "2h", "1h30"
            match = re.match(r'(\d+)h(\d+)?', duree_str)
            if match:
                heures = int(match.group(1))
                minutes = int(match.group(2)) if match.group(2) else 0
                return Decimal(str(heures + minutes / 60))
        elif 'min' in duree_str:
            # Ex: "30 min", "45 min"
            match = re.match(r'(\d+)', duree_str)
            if match:
                minutes = int(match.group(1))
                return Decimal(str(minutes / 60))

        return Decimal('1.0')  # Défaut

    def extract_nb_seances(self, nom_prestation):
        """Extrait le nombre de séances d'un nom de forfait"""
        nom_lower = nom_prestation.lower()

        # Patterns courants
        patterns = [
            r'(\d+)\s*séances?',
            r'(\d+)\s*sÃ©ances?',  # Encodage UTF-8 cassé
            r'forfait\s*(\d+)',
            r'cure\s*(\d+)',
            r'(\d+)\s*jours',
        ]

        for pattern in patterns:
            match = re.search(pattern, nom_lower)
            if match:
                return int(match.group(1))

        # Cas spéciaux
        if 'cure' in nom_lower and 'corrective' in nom_lower:
            return 6  # Bloomea cure corrective
        if 'vaccum' in nom_lower and 'cure' in nom_lower:
            return 6  # Vaccum cure

        return 1

    def handle(self, *args, **options):
        csv_path = options['csv']
        dry_run = options['dry_run']

        self.stdout.write(f"Lecture du fichier {csv_path}...")

        # Couleurs pour les familles
        couleurs = [
            '#e8b4b8', '#b4d4e8', '#b8e8b4', '#e8d4b4', '#d4b4e8',
            '#e8e8b4', '#b4e8e8', '#e8b4d4', '#c4d4b4', '#d4b4c4',
            '#b4c4e8', '#e8c4b4', '#c4e8b4', '#b4e8c4', '#e8b4c4',
        ]
        couleur_index = 0

        stats = {
            'familles_creees': 0,
            'prestations_creees': 0,
            'prestations_mises_a_jour': 0,
            'options_creees': 0,
            'options_mises_a_jour': 0,
        }

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')

                for row in reader:
                    institut_nom = row['Institut'].strip()
                    famille_nom = row['Famille_prestation'].strip()
                    prestation_nom = row['Prestation'].strip()
                    duree_str = row['Duree'].strip() if row['Duree'] else ''
                    prix = int(row['Prix']) if row['Prix'] else 0
                    est_option = row['Option'].strip() == '1'
                    est_forfait = row['Forfait'].strip() == '1'

                    # Récupérer l'institut
                    institut_code = {
                        'Palais': 'palais',
                        'Klinic': 'klinic',
                        'Express': 'express'
                    }.get(institut_nom)

                    if not institut_code:
                        self.stdout.write(self.style.WARNING(
                            f"Institut inconnu: {institut_nom}"
                        ))
                        continue

                    try:
                        institut = Institut.objects.get(code=institut_code)
                    except Institut.DoesNotExist:
                        self.stdout.write(self.style.ERROR(
                            f"Institut {institut_code} n'existe pas en base"
                        ))
                        continue

                    if est_option:
                        # Traitement des OPTIONS
                        if not dry_run:
                            option, created = Option.objects.update_or_create(
                                nom=prestation_nom,
                                institut=institut,
                                defaults={
                                    'prix': prix,
                                    'a_quantite': True,  # La plupart ont une quantité
                                    'actif': True,
                                }
                            )
                            if created:
                                stats['options_creees'] += 1
                                self.stdout.write(self.style.SUCCESS(
                                    f"  + Option créée: {prestation_nom} ({prix} CFA)"
                                ))
                            else:
                                stats['options_mises_a_jour'] += 1
                                self.stdout.write(
                                    f"  ~ Option mise à jour: {prestation_nom} ({prix} CFA)"
                                )
                        else:
                            self.stdout.write(
                                f"  [DRY-RUN] Option: {prestation_nom} ({prix} CFA)"
                            )
                    else:
                        # Traitement des PRESTATIONS

                        # Créer ou récupérer la famille
                        if not dry_run:
                            famille, famille_created = FamillePrestation.objects.get_or_create(
                                nom=famille_nom,
                                institut=institut,
                                defaults={
                                    'couleur': couleurs[couleur_index % len(couleurs)],
                                    'ordre_affichage': 0,
                                }
                            )
                            if famille_created:
                                stats['familles_creees'] += 1
                                couleur_index += 1
                                self.stdout.write(self.style.SUCCESS(
                                    f"+ Famille créée: {famille_nom} ({institut_nom})"
                                ))

                        # Calculer la durée
                        duree = self.parse_duree(duree_str)

                        # Nombre de séances pour les forfaits
                        nb_seances = 1
                        if est_forfait:
                            nb_seances = self.extract_nb_seances(prestation_nom)

                        if not dry_run:
                            prestation, created = Prestation.objects.update_or_create(
                                nom=prestation_nom,
                                famille=famille,
                                defaults={
                                    'duree': duree,
                                    'prix': prix,
                                    'actif': True,
                                    'est_forfait': est_forfait,
                                    'nombre_seances': nb_seances,
                                }
                            )

                            forfait_info = f" [FORFAIT {nb_seances} séances]" if est_forfait else ""

                            if created:
                                stats['prestations_creees'] += 1
                                self.stdout.write(self.style.SUCCESS(
                                    f"  + Prestation créée: {prestation_nom} ({prix} CFA){forfait_info}"
                                ))
                            else:
                                stats['prestations_mises_a_jour'] += 1
                                self.stdout.write(
                                    f"  ~ Prestation mise à jour: {prestation_nom} ({prix} CFA){forfait_info}"
                                )
                        else:
                            forfait_info = f" [FORFAIT {nb_seances} séances]" if est_forfait else ""
                            self.stdout.write(
                                f"  [DRY-RUN] Prestation: {prestation_nom} ({prix} CFA){forfait_info}"
                            )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Fichier non trouvé: {csv_path}"))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur: {str(e)}"))
            raise

        # Résumé
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("RÉSUMÉ:"))
        self.stdout.write(f"  Familles créées: {stats['familles_creees']}")
        self.stdout.write(f"  Prestations créées: {stats['prestations_creees']}")
        self.stdout.write(f"  Prestations mises à jour: {stats['prestations_mises_a_jour']}")
        self.stdout.write(f"  Options créées: {stats['options_creees']}")
        self.stdout.write(f"  Options mises à jour: {stats['options_mises_a_jour']}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY-RUN] Aucune modification appliquée"))

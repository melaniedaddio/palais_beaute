from django.core.management.base import BaseCommand
from core.models import *


class Command(BaseCommand):
    help = 'Initialise les données de base'

    def handle(self, *args, **options):
        self.stdout.write("Création des instituts...")

        # Créer les instituts
        palais, created = Institut.objects.get_or_create(
            code="palais",
            defaults={
                'nom': "Le Palais",
                'a_agenda': True,
                'heure_ouverture': "07:00",
                'heure_fermeture': "23:00",
                'fond_caisse': 30000
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'[OK] Institut "{palais.nom}" cree'))

        klinic, created = Institut.objects.get_or_create(
            code="klinic",
            defaults={
                'nom': "La Klinic",
                'a_agenda': True,
                'heure_ouverture': "07:00",
                'heure_fermeture': "23:00",
                'fond_caisse': 30000
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'[OK] Institut "{klinic.nom}" cree'))

        express, created = Institut.objects.get_or_create(
            code="express",
            defaults={
                'nom': "Express",
                'a_agenda': False,
                'heure_ouverture': "07:00",
                'heure_fermeture': "23:00",
                'fond_caisse': 30000
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'[OK] Institut "{express.nom}" cree'))

        # Créer les employés Le Palais
        self.stdout.write("\nCréation des employés Le Palais...")
        employes_palais = [
            'Marthe', 'Brigitte', 'Jeanette', 'Lilianne', 'Maria',
            'Sintich', 'Nadia', 'Moye', 'Angela', 'Zahra', 'Béa',
            'Estelle', 'Anna', 'Nadeige', 'Fati', 'Shella',
            'Josianne', 'Grace', 'Fidèle', 'Emma', 'Kadi'
        ]
        for i, nom in enumerate(employes_palais):
            _, created = Employe.objects.get_or_create(
                nom=nom,
                institut=palais,
                defaults={'ordre_affichage': i}
            )
            if created:
                self.stdout.write(f'  [OK] {nom}')

        # Créer les employés La Klinic
        self.stdout.write("\nCréation des employés La Klinic...")
        employes_klinic = ['Maria', 'Joyce', 'Saly', 'Bb', 'Audrey', 'Milan', 'Infra']
        for i, nom in enumerate(employes_klinic):
            _, created = Employe.objects.get_or_create(
                nom=nom,
                institut=klinic,
                defaults={'ordre_affichage': i}
            )
            if created:
                self.stdout.write(f'  [OK] {nom}')

        # Créer les employés Express
        self.stdout.write("\nCréation des employés Express...")
        employes_express = ['Chad', 'Emi', 'Elise', 'Laurene', 'Estelle']
        for i, nom in enumerate(employes_express):
            _, created = Employe.objects.get_or_create(
                nom=nom,
                institut=express,
                defaults={'ordre_affichage': i}
            )
            if created:
                self.stdout.write(f'  [OK] {nom}')

        # Créer les prestations pour Le Palais
        self.stdout.write("\nCréation des prestations Le Palais...")
        self.create_prestations_palais(palais)

        # Créer les prestations pour La Klinic
        self.stdout.write("\nCréation des prestations La Klinic...")
        self.create_prestations_klinic(klinic)

        # Créer les prestations pour Express
        self.stdout.write("\nCréation des prestations Express...")
        self.create_prestations_express(express)

        # Créer les options
        self.stdout.write("\nCréation des options...")
        self.create_options(palais, klinic)

        self.stdout.write(self.style.SUCCESS('\n[SUCCES] Données initiales créées avec succès!'))

    def create_prestations_palais(self, institut):
        """Crée toutes les prestations pour Le Palais"""

        # 1. Ongle
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Ongle", institut=institut,
            defaults={'couleur': '#e8b4b8', 'ordre_affichage': 1}
        )
        prestations = [
            ("Manucure", 1, 5000),
            ("Manucure + pose vernis", 1, 8000),
            ("Beauté des pieds", 1, 5000),
            ("Beauté des pieds + pose vernis", 1, 8000),
            ("Manucure + Beauté des pieds + pose vernis", 1, 15000),
            ("Pose de vernis simple main ou pied", 0.5, 5000),
            ("Massage de main ou pied", 0.25, 6000),
        ]
        self._create_prestations(famille, prestations)

        # 2. Vernis semi permanent
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Vernis semi permanent", institut=institut,
            defaults={'couleur': '#d4a5a5', 'ordre_affichage': 2}
        )
        prestations = [
            ("Semi permanent main", 1, 18000),
            ("Semi permanent pied", 1, 18000),
            ("Semi permanent main + pied", 1.5, 30000),
            ("Retrait semi permanent", 0.5, 5000),
        ]
        self._create_prestations(famille, prestations)

        # 3. Gel
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Gel", institut=institut,
            defaults={'couleur': '#f0a08a', 'ordre_affichage': 3}
        )
        prestations = [
            ("Pose gel des mains couleur", 2, 45000),
            ("Pose gel des mains french", 2, 45000),
            ("Pose gel des pieds couleur", 2, 45000),
            ("Pose gel des pieds french", 2, 45000),
            ("Remplissage gel main ou pied", 1.5, 30000),
            ("Retrait gel", 0.5, 10000),
        ]
        self._create_prestations(famille, prestations)

        # 4. Laser femme
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Laser femme", institut=institut,
            defaults={'couleur': '#b8a9c9', 'ordre_affichage': 4}
        )
        prestations = [
            ("Lèvre supérieure", 0.25, 20000),
            ("Joue", 0.25, 20000),
            ("Menton", 0.25, 20000),
            ("Sourcils", 0.25, 10000),
            ("Front", 0.25, 10000),
            ("Favoris", 0.25, 10000),
            ("Cou", 0.25, 20000),
            ("Aisselles", 0.25, 30000),
            ("Demi bras", 0.5, 40000),
            ("Bras complet", 0.5, 60000),
            ("Mains", 0.25, 20000),
            ("Doigts", 0.25, 20000),
            ("Dos", 1, 80000),
            ("Épaules", 0.5, 40000),
            ("Ventre", 0.5, 40000),
            ("Ligne blanche", 0.25, 10000),
            ("Sillon interfessier", 0.5, 30000),
            ("Maillot simple", 0.5, 35000),
            ("Maillot échancré", 0.5, 45000),
            ("Maillot intégral", 0.75, 60000),
            ("Demi jambes", 1, 60000),
            ("Jambes complètes", 1.5, 100000),
            ("Pieds", 0.25, 20000),
            ("Orteils", 0.25, 20000),
        ]
        self._create_prestations(famille, prestations)

        # 5. Laser homme
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Laser homme", institut=institut,
            defaults={'couleur': '#8fa5b8', 'ordre_affichage': 5}
        )
        prestations = [
            ("Barbe complète", 0.5, 50000),
            ("Contour de barbe", 0.25, 30000),
            ("Cou", 0.25, 30000),
            ("Torse", 1, 80000),
            ("Ventre", 0.5, 50000),
            ("Dos", 1, 100000),
            ("Épaules", 0.5, 50000),
            ("Aisselles", 0.25, 40000),
            ("Bras complet", 0.75, 80000),
        ]
        self._create_prestations(famille, prestations)

        # 6. Soin médicaux corps amincissant
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Soin médicaux corps amincissant", institut=institut,
            defaults={'couleur': '#7ec8c8', 'ordre_affichage': 6}
        )
        prestations = [
            ("Cryo 1 zone", 1, 170000),
            ("Cryo 2 zones", 1.5, 255000),
            ("Cryo 3 zones", 2, 340000),
            ("Cryo 4 zones", 2.5, 425000),
            ("Cryo 5 zones", 3, 510000),
        ]
        self._create_prestations(famille, prestations)

        # 7. Vaccum
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Vaccum", institut=institut,
            defaults={'couleur': '#98d4bb', 'ordre_affichage': 7}
        )
        prestations = [
            ("Vaccum 1 zone", 0.5, 30000),
            ("Vaccum 2 zones", 0.75, 45000),
            ("Vaccum 3 zones", 1, 60000),
        ]
        self._create_prestations(famille, prestations)

        # 8. Body sculte
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Body sculte", institut=institut,
            defaults={'couleur': '#a8c69f', 'ordre_affichage': 8}
        )
        prestations = [
            ("Body sculte 1 zone", 1, 60000),
            ("Body sculte 2 zones", 1.5, 90000),
        ]
        self._create_prestations(famille, prestations)

        # 9. Infra bike
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Infra bike", institut=institut,
            defaults={'couleur': '#f5c396', 'ordre_affichage': 9}
        )
        prestations = [
            ("Infra bike", 0.5, 25000),
        ]
        self._create_prestations(famille, prestations)

        # 10. Traitement vergeture
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Traitement vergeture", institut=institut,
            defaults={'couleur': '#c9b8db', 'ordre_affichage': 10}
        )
        prestations = [
            ("Traitement vergeture 1 zone", 1, 100000),
        ]
        self._create_prestations(famille, prestations)

        # 11. Soin médicaux visage
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Soin médicaux visage", institut=institut,
            defaults={'couleur': '#e6c8b8', 'ordre_affichage': 11}
        )
        prestations = [
            ("Hollywood peel", 1, 80000),
            ("Peeling", 1, 50000),
            ("Masque led", 0.5, 30000),
        ]
        self._create_prestations(famille, prestations)

        # 12. Bloomea Paris
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Bloomea Paris", institut=institut,
            defaults={'couleur': '#d4af7a', 'ordre_affichage': 12}
        )
        prestations = [
            ("Soin visage Bloomea", 1.5, 50000),
            ("Soin corps Bloomea", 2, 70000),
        ]
        self._create_prestations(famille, prestations)

        # 13. Jetpeel
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Jetpeel", institut=institut,
            defaults={'couleur': '#a8d4e6', 'ordre_affichage': 13}
        )
        prestations = [
            ("Jetpeel visage", 1, 60000),
            ("Jetpeel corps 1 zone", 1, 70000),
        ]
        self._create_prestations(famille, prestations)

        # 14. Morpheus 8
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Morpheus 8", institut=institut,
            defaults={'couleur': '#9d7a8c', 'ordre_affichage': 14}
        )
        prestations = [
            ("Morpheus 8 visage", 1.5, 200000),
            ("Morpheus 8 corps 1 zone", 1.5, 250000),
        ]
        self._create_prestations(famille, prestations)

        # 15. LPG
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="LPG", institut=institut,
            defaults={'couleur': '#9dd4c4', 'ordre_affichage': 15}
        )
        prestations = [
            ("LPG corps", 1, 30000),
            ("LPG visage", 0.5, 25000),
        ]
        self._create_prestations(famille, prestations)

        # 16. Soin profond
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Soin profond", institut=institut,
            defaults={'couleur': '#e8d4c8', 'ordre_affichage': 16}
        )
        prestations = [
            ("Nettoyage de peau", 1, 25000),
            ("Soin hydratant", 1, 30000),
            ("Soin anti-âge", 1.5, 40000),
        ]
        self._create_prestations(famille, prestations)

        # 17. Soin epilation cire femme
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Soin epilation cire femme", institut=institut,
            defaults={'couleur': '#f8c8b4', 'ordre_affichage': 17}
        )
        prestations = [
            ("Sourcils", 0.25, 5000),
            ("Lèvre", 0.25, 3000),
            ("Menton", 0.25, 3000),
            ("Visage complet", 0.5, 8000),
            ("Aisselles", 0.25, 5000),
            ("Bras", 0.5, 10000),
            ("Demi jambes", 0.5, 10000),
            ("Jambes complètes", 1, 15000),
            ("Maillot simple", 0.5, 8000),
            ("Maillot échancré", 0.5, 10000),
            ("Maillot intégral", 0.75, 15000),
        ]
        self._create_prestations(famille, prestations)

        # 18. Soin epilation cire homme
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Soin epilation cire homme", institut=institut,
            defaults={'couleur': '#b8a898', 'ordre_affichage': 18}
        )
        prestations = [
            ("Dos", 1, 20000),
            ("Torse", 0.75, 15000),
            ("Bras", 0.5, 12000),
            ("Jambes", 1, 20000),
        ]
        self._create_prestations(famille, prestations)

        self.stdout.write(self.style.SUCCESS('  [OK] Prestations Le Palais créées'))

    def create_prestations_klinic(self, institut):
        """Crée toutes les prestations pour La Klinic"""

        # 1. Laser femme
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Laser femme", institut=institut,
            defaults={'couleur': '#b8a9c9', 'ordre_affichage': 1}
        )
        prestations = [
            ("Lèvre supérieure", 0.25, 20000),
            ("Joue", 0.25, 20000),
            ("Menton", 0.25, 20000),
            ("Sourcils", 0.25, 10000),
            ("Front", 0.25, 10000),
            ("Favoris", 0.25, 10000),
            ("Cou", 0.25, 20000),
            ("Aisselles", 0.25, 30000),
            ("Demi bras", 0.5, 40000),
            ("Bras complet", 0.5, 60000),
            ("Mains", 0.25, 20000),
            ("Doigts", 0.25, 20000),
            ("Dos", 1, 80000),
            ("Épaules", 0.5, 40000),
            ("Ventre", 0.5, 40000),
            ("Ligne blanche", 0.25, 10000),
            ("Sillon interfessier", 0.5, 30000),
            ("Maillot simple", 0.5, 35000),
            ("Maillot échancré", 0.5, 45000),
            ("Maillot intégral", 0.75, 60000),
            ("Demi jambes", 1, 60000),
            ("Jambes complètes", 1.5, 100000),
            ("Pieds", 0.25, 20000),
            ("Orteils", 0.25, 20000),
        ]
        self._create_prestations(famille, prestations)

        # 2. Laser homme
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Laser homme", institut=institut,
            defaults={'couleur': '#8fa5b8', 'ordre_affichage': 2}
        )
        prestations = [
            ("Barbe complète", 0.5, 50000),
            ("Contour de barbe", 0.25, 30000),
            ("Cou", 0.25, 30000),
            ("Torse", 1, 80000),
            ("Ventre", 0.5, 50000),
            ("Dos", 1, 100000),
            ("Épaules", 0.5, 50000),
            ("Aisselles", 0.25, 40000),
            ("Bras complet", 0.75, 80000),
        ]
        self._create_prestations(famille, prestations)

        # 3. Soin médicaux corps amincissant
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Soin médicaux corps amincissant", institut=institut,
            defaults={'couleur': '#7ec8c8', 'ordre_affichage': 3}
        )
        prestations = [
            ("Cryo 1 zone", 1, 170000),
            ("Cryo 2 zones", 1.5, 255000),
            ("Cryo 3 zones", 2, 340000),
            ("Cryo 4 zones", 2.5, 425000),
            ("Cryo 5 zones", 3, 510000),
        ]
        self._create_prestations(famille, prestations)

        # 4. Vaccum
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Vaccum", institut=institut,
            defaults={'couleur': '#98d4bb', 'ordre_affichage': 4}
        )
        prestations = [
            ("Vaccum 1 zone", 0.5, 30000),
            ("Vaccum 2 zones", 0.75, 45000),
            ("Vaccum 3 zones", 1, 60000),
        ]
        self._create_prestations(famille, prestations)

        # 5. Body sculte
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Body sculte", institut=institut,
            defaults={'couleur': '#a8c69f', 'ordre_affichage': 5}
        )
        prestations = [
            ("Body sculte 1 zone", 1, 60000),
            ("Body sculte 2 zones", 1.5, 90000),
        ]
        self._create_prestations(famille, prestations)

        # 6. Infra bike
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Infra bike", institut=institut,
            defaults={'couleur': '#f5c396', 'ordre_affichage': 6}
        )
        prestations = [
            ("Infra bike", 0.5, 25000),
        ]
        self._create_prestations(famille, prestations)

        # 7. Traitement vergeture
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Traitement vergeture", institut=institut,
            defaults={'couleur': '#c9b8db', 'ordre_affichage': 7}
        )
        prestations = [
            ("Traitement vergeture 1 zone", 1, 100000),
        ]
        self._create_prestations(famille, prestations)

        # 8. Soin médicaux visage
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Soin médicaux visage", institut=institut,
            defaults={'couleur': '#e6c8b8', 'ordre_affichage': 8}
        )
        prestations = [
            ("Hollywood peel", 1, 80000),
            ("Peeling", 1, 50000),
            ("Masque led", 0.5, 30000),
        ]
        self._create_prestations(famille, prestations)

        # 9. Bloomea Paris
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Bloomea Paris", institut=institut,
            defaults={'couleur': '#d4af7a', 'ordre_affichage': 9}
        )
        prestations = [
            ("Soin visage Bloomea", 1.5, 50000),
            ("Soin corps Bloomea", 2, 70000),
        ]
        self._create_prestations(famille, prestations)

        # 10. Jetpeel
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Jetpeel", institut=institut,
            defaults={'couleur': '#a8d4e6', 'ordre_affichage': 10}
        )
        prestations = [
            ("Jetpeel visage", 1, 60000),
            ("Jetpeel corps 1 zone", 1, 70000),
        ]
        self._create_prestations(famille, prestations)

        # 11. Morpheus 8
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Morpheus 8", institut=institut,
            defaults={'couleur': '#9d7a8c', 'ordre_affichage': 11}
        )
        prestations = [
            ("Morpheus 8 visage", 1.5, 200000),
            ("Morpheus 8 corps 1 zone", 1.5, 250000),
        ]
        self._create_prestations(famille, prestations)

        # 12. LPG
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="LPG", institut=institut,
            defaults={'couleur': '#9dd4c4', 'ordre_affichage': 12}
        )
        prestations = [
            ("LPG corps", 1, 30000),
            ("LPG visage", 0.5, 25000),
        ]
        self._create_prestations(famille, prestations)

        # 13. Soin profond
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Soin profond", institut=institut,
            defaults={'couleur': '#e8d4c8', 'ordre_affichage': 13}
        )
        prestations = [
            ("Nettoyage de peau", 1, 25000),
            ("Soin hydratant", 1, 30000),
            ("Soin anti-âge", 1.5, 40000),
        ]
        self._create_prestations(famille, prestations)

        # 14. Soin epilation cire femme
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Soin epilation cire femme", institut=institut,
            defaults={'couleur': '#f8c8b4', 'ordre_affichage': 14}
        )
        prestations = [
            ("Sourcils", 0.25, 5000),
            ("Lèvre", 0.25, 3000),
            ("Menton", 0.25, 3000),
            ("Visage complet", 0.5, 8000),
            ("Aisselles", 0.25, 5000),
            ("Bras", 0.5, 10000),
            ("Demi jambes", 0.5, 10000),
            ("Jambes complètes", 1, 15000),
            ("Maillot simple", 0.5, 8000),
            ("Maillot échancré", 0.5, 10000),
            ("Maillot intégral", 0.75, 15000),
        ]
        self._create_prestations(famille, prestations)

        # 15. Soin epilation cire homme
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Soin epilation cire homme", institut=institut,
            defaults={'couleur': '#b8a898', 'ordre_affichage': 15}
        )
        prestations = [
            ("Dos", 1, 20000),
            ("Torse", 0.75, 15000),
            ("Bras", 0.5, 12000),
            ("Jambes", 1, 20000),
        ]
        self._create_prestations(famille, prestations)

        self.stdout.write(self.style.SUCCESS('  [OK] Prestations La Klinic créées'))

    def create_prestations_express(self, institut):
        """Crée toutes les prestations pour Express"""

        # 1. Coiffure
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Coiffure", institut=institut,
            defaults={'couleur': '#e8b4b8', 'ordre_affichage': 1}
        )
        prestations = [
            ("Petite coupe", 0.5, 20000, None),
            ("Grosse coupe", 0.75, 30000, None),
            ("Brushing cheveux court", 0.5, 10000, None),
            ("Brushing + fer", 0.5, 13000, None),
            ("Brushing cheveux long", 0.75, 15000, None),
            ("Boucles", 0.5, 13000, None),
            ("Shampoing", 0.25, 5000, None),
            ("Racine", 1, 30000, None),
            ("Couleur cheveux court", 1.5, 40000, None),
            ("Couleur cheveux long", 2, 60000, None),
            ("Conturing", 1, 30000, None),
            ("Rinçage", 0.75, 25000, None),
            ("Low light cheveux court", 1.5, 60000, None),
            ("Low light cheveux long", 2, 80000, None),
            ("High light cheveux court", 2, 80000, None),
            ("High light cheveux long", 3, 160000, None),
            ("Chignon", 1.5, 40000, None),
            ("Demi relevé", 1, 25000, None),
            ("Coiffure engagement", 2, 80000, None),
            ("Mariage", 3, 150000, None),
            ("Soin olaplex", 1, 30000, None),
            ("Bain d'huile", 0.75, 20000, None),
        ]
        self._create_prestations_with_unite(famille, prestations)

        # 2. Coiffure afro
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Coiffure afro", institut=institut,
            defaults={'couleur': '#c9a07a', 'ordre_affichage': 2}
        )
        prestations = [
            ("Fer", 0.75, 20000, None),
            ("Shampoing + brushing", 0.5, 15000, None),
            ("Défrisage", 1, 30000, None),
            ("Défaire tresses simples", 0.5, 5000, None),
            ("Défaire tresses compliquées", 0.75, 10000, None),
            ("Napo", 0.5, 10000, None),
            ("Shampoing traitement", 0.75, 20000, None),
            ("Shampoing simple", 0.25, 5000, None),
            ("Tissage", 1, 15000, "/boules"),
            ("Nattes simples", 1, 10000, None),
            ("Nattes modèles", 1.5, 20000, None),
            ("Mise en forme", 0.5, 10000, None),
            ("Coupe", 0.75, 25000, None),
            ("Couleur", 1.5, 45000, None),
            ("Couleur + extensions", 2, 80000, None),
        ]
        self._create_prestations_with_unite(famille, prestations)

        # 3. Lissage kératine
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Lissage kératine", institut=institut,
            defaults={'couleur': '#d4af7a', 'ordre_affichage': 3}
        )
        prestations = [
            ("Cheveux courts", 2, 100000, None),
            ("Cheveux mi-long", 2.5, 160000, None),
            ("Cheveux long", 3, 200000, None),
        ]
        self._create_prestations_with_unite(famille, prestations)

        # 4. Extensions
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Extensions", institut=institut,
            defaults={'couleur': '#c9987a', 'ordre_affichage': 4}
        )
        prestations = [
            ("Un paquet", 2, 150000, None),
            ("Dépose", 0.5, 700, "/mèches"),
            ("Colle + pose", 0.5, 1000, "/mèches"),
            ("Colle", 0.25, 700, "/mèches"),
        ]
        self._create_prestations_with_unite(famille, prestations)

        self.stdout.write(self.style.SUCCESS('  [OK] Prestations Express créées'))

    def create_options(self, palais, klinic):
        """Crée les options pour les instituts"""

        # Options Le Palais
        options_palais = [
            ("Strass", 1000, True, "strass"),
            ("Dessin", 1000, True, "ongle"),
            ("Effet miroir", 15000, False, None),
            ("Babyboomer", 15000, False, None),
            ("Déco spéciale", 5000, True, "ongle"),
            ("Jelly spa", 5000, False, None),
        ]
        for nom, prix, a_quantite, unite in options_palais:
            _, created = Option.objects.get_or_create(
                nom=nom,
                institut=palais,
                defaults={
                    'prix': prix,
                    'a_quantite': a_quantite,
                    'unite': unite
                }
            )
            if created:
                self.stdout.write(f'  [OK] Option "{nom}" pour Le Palais')

        # Options La Klinic
        _, created = Option.objects.get_or_create(
            nom="LPG Collant",
            institut=klinic,
            defaults={
                'prix': 15000,
                'a_quantite': False,
                'unite': None
            }
        )
        if created:
            self.stdout.write(f'  [OK] Option "LPG Collant" pour La Klinic')

    def _create_prestations(self, famille, prestations):
        """Méthode helper pour créer les prestations"""
        for i, (nom, duree, prix) in enumerate(prestations):
            Prestation.objects.get_or_create(
                nom=nom,
                famille=famille,
                defaults={
                    'duree': duree,
                    'prix': prix,
                    'ordre_affichage': i
                }
            )

    def _create_prestations_with_unite(self, famille, prestations):
        """Méthode helper pour créer les prestations avec unité"""
        for i, data in enumerate(prestations):
            nom, duree, prix, unite = data
            Prestation.objects.get_or_create(
                nom=nom,
                famille=famille,
                defaults={
                    'duree': duree,
                    'prix': prix,
                    'unite': unite,
                    'ordre_affichage': i
                }
            )

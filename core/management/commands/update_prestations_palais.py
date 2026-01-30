from django.core.management.base import BaseCommand
from core.models import Institut, FamillePrestation, Prestation


class Command(BaseCommand):
    help = 'Met à jour les prestations du Palais avec les nouvelles familles et prestations'

    def handle(self, *args, **options):
        self.stdout.write("Mise à jour des prestations du Palais...")

        # Récupérer l'institut Le Palais
        try:
            palais = Institut.objects.get(code="palais")
        except Institut.DoesNotExist:
            self.stdout.write(self.style.ERROR('Institut "Le Palais" non trouvé!'))
            return

        # Désactiver toutes les anciennes prestations du Palais (pour ne pas les supprimer)
        self.stdout.write("Désactivation des anciennes prestations...")
        Prestation.objects.filter(famille__institut=palais).update(actif=False)

        # Supprimer les anciennes familles du Palais (sauf celles qui ont des RDV)
        self.stdout.write("Nettoyage des anciennes familles...")
        anciennes_familles = FamillePrestation.objects.filter(institut=palais)
        for famille in anciennes_familles:
            # Garder les familles qui ont des prestations utilisées dans des RDV
            if not famille.prestations.filter(rendez_vous__isnull=False).exists():
                famille.delete()
                self.stdout.write(f'  [OK] Famille "{famille.nom}" supprimée')

        # 1. Ongle
        self.stdout.write("\nCréation de la famille Ongle...")
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Ongle", institut=palais,
            defaults={'couleur': '#e8b4b8', 'ordre_affichage': 1}
        )
        prestations = [
            ("Manucure", 1, 5000),
            ("Manucure + pose vernis", 1, 8000),
            ("Beauté des pied", 1, 5000),
            ("Beauté des pied + pose vernis", 1, 8000),
            ("Manucure + Beauté des pied + pose vernis", 1, 15000),
            ("Pose de vernis simple main ou pied", 0.5, 5000),
            ("Massage de main ou pied", 0.25, 6000),
        ]
        self._create_prestations(famille, prestations)
        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(prestations)} prestations créées pour Ongle'))

        # 2. Vernis semi permanent
        self.stdout.write("\nCréation de la famille Vernis semi permanent...")
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Vernis semi permanent", institut=palais,
            defaults={'couleur': '#d4a5a5', 'ordre_affichage': 2}
        )
        prestations = [
            ("Vernis semi permanant main ou pied couleur", 1, 10000),
            ("Vernis semi permanant main ou pied French", 1, 15000),
            ("Depose de semi permanent", 0.5, 5000),
        ]
        self._create_prestations(famille, prestations)
        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(prestations)} prestations créées pour Vernis semi permanent'))

        # 3. Gel
        self.stdout.write("\nCréation de la famille Gel...")
        famille, _ = FamillePrestation.objects.get_or_create(
            nom="Gel", institut=palais,
            defaults={'couleur': '#f0a08a', 'ordre_affichage': 3}
        )
        prestations = [
            ("Pose gel des mains couleur ou French", 2, 45000),
            ("Pose gel des mains babyboomer", 2, 60000),
            ("Pose gel des mains couleur ou french avec capsule", 2, 65000),
            ("Pose gel des mains babyboomer avec capsule", 2, 80000),
            ("Pose gel des pieds couleur ou French", 1, 35000),
            ("Remplissage des mains couleur", 2, 30000),
            ("Remplissage des mains French", 2, 35000),
            ("Remplissage des mains babyboomer", 2, 40000),
            ("Remplissage des pieds couleur ou French", 1, 25000),
            ("Beauté des mains ou pieds couleur", 1, 20000),
            ("Beauté des mains ou pieds French", 1, 25000),
            ("Réparation un ongle", 0.5, 3000),
            ("Depose de gel", 1, 10000),
        ]
        self._create_prestations(famille, prestations)
        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(prestations)} prestations créées pour Gel'))

        self.stdout.write(self.style.SUCCESS('\n[SUCCES] Prestations du Palais mises à jour avec succès!'))
        self.stdout.write(self.style.SUCCESS('Total: 3 familles et 23 prestations'))

    def _create_prestations(self, famille, prestations):
        """Méthode helper pour créer les prestations"""
        for i, (nom, duree, prix) in enumerate(prestations):
            Prestation.objects.update_or_create(
                nom=nom,
                famille=famille,
                defaults={
                    'duree': duree,
                    'prix': prix,
                    'actif': True,
                    'ordre_affichage': i
                }
            )

from django.core.management.base import BaseCommand
from core.models import Institut, FamillePrestation


class Command(BaseCommand):
    help = 'Nettoie les familles de prestations inutilisées du Palais'

    def handle(self, *args, **options):
        self.stdout.write("Nettoyage des familles du Palais...")

        # Récupérer l'institut Le Palais
        try:
            palais = Institut.objects.get(code="palais")
        except Institut.DoesNotExist:
            self.stdout.write(self.style.ERROR('Institut "Le Palais" non trouvé!'))
            return

        # Familles à conserver
        familles_a_conserver = ["Ongle", "Vernis semi permanent", "Gel"]

        # Récupérer toutes les familles du Palais
        toutes_familles = FamillePrestation.objects.filter(institut=palais)

        for famille in toutes_familles:
            if famille.nom not in familles_a_conserver:
                # Vérifier si cette famille a des prestations utilisées dans des RDV
                prestations_avec_rdv = famille.prestations.filter(rendez_vous__isnull=False).exists()

                if prestations_avec_rdv:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  [SKIP] Famille "{famille.nom}" conservée (utilisée dans des RDV existants)'
                        )
                    )
                else:
                    # Supprimer d'abord toutes les prestations de cette famille
                    nb_prestations = famille.prestations.count()
                    famille.prestations.all().delete()

                    # Puis supprimer la famille
                    famille.delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [OK] Famille "{famille.nom}" supprimée ({nb_prestations} prestations)'
                        )
                    )

        # Afficher les familles restantes
        self.stdout.write("\nFamilles du Palais restantes:")
        familles_restantes = FamillePrestation.objects.filter(institut=palais).order_by('ordre_affichage')
        for fam in familles_restantes:
            nb_prestations = fam.prestations.filter(actif=True).count()
            self.stdout.write(f'  - {fam.nom} ({nb_prestations} prestations actives)')

        self.stdout.write(self.style.SUCCESS('\n[SUCCES] Nettoyage terminé!'))

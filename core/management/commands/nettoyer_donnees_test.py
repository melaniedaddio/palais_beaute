"""
Commande Django pour nettoyer toutes les données de test
et remettre la base de données dans un état propre pour la production.

Usage: python manage.py nettoyer_donnees_test
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import (
    RendezVous, RendezVousOption, Paiement, CarteCadeau,
    ForfaitClient, SeanceForfait, ModificationLog, ClotureCaisse,
    PaiementCredit, Credit
)


class Command(BaseCommand):
    help = 'Nettoie toutes les données de test (RDV, paiements, cartes cadeaux, forfaits)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmer la suppression sans demander',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('⚠️  ATTENTION : Cette opération va supprimer toutes les données de test !'))
        self.stdout.write('')
        self.stdout.write('Les données suivantes seront supprimées :')
        self.stdout.write(f'  - Rendez-vous : {RendezVous.objects.count()}')
        self.stdout.write(f'  - Paiements : {Paiement.objects.count()}')
        self.stdout.write(f'  - Cartes cadeaux : {CarteCadeau.objects.count()}')
        self.stdout.write(f'  - Forfaits clients : {ForfaitClient.objects.count()}')
        self.stdout.write(f'  - Crédits : {Credit.objects.count()}')
        self.stdout.write(f'  - Clôtures de caisse : {ClotureCaisse.objects.count()}')
        self.stdout.write(f'  - Logs de modifications : {ModificationLog.objects.count()}')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Les données de configuration (instituts, employés, prestations, options, clients) seront CONSERVÉES.'))
        self.stdout.write('')

        if not options['confirm']:
            confirmation = input('Voulez-vous vraiment continuer ? Tapez "OUI" en majuscules pour confirmer : ')
            if confirmation != 'OUI':
                self.stdout.write(self.style.ERROR('❌ Opération annulée'))
                return

        self.stdout.write('')
        self.stdout.write('🔄 Nettoyage en cours...')
        self.stdout.write('')

        try:
            with transaction.atomic():
                # 1. Supprimer les séances de forfait (avant les forfaits)
                count_seances = SeanceForfait.objects.count()
                SeanceForfait.objects.all().delete()
                self.stdout.write(f'✓ {count_seances} séances de forfait supprimées')

                # 2. Supprimer les forfaits clients
                count_forfaits = ForfaitClient.objects.count()
                ForfaitClient.objects.all().delete()
                self.stdout.write(f'✓ {count_forfaits} forfaits clients supprimés')

                # 3. Supprimer les cartes cadeaux
                count_cartes = CarteCadeau.objects.count()
                CarteCadeau.objects.all().delete()
                self.stdout.write(f'✓ {count_cartes} cartes cadeaux supprimées')

                # 4. Supprimer les paiements de crédits
                count_paiements_credit = PaiementCredit.objects.count()
                PaiementCredit.objects.all().delete()
                self.stdout.write(f'✓ {count_paiements_credit} paiements de crédits supprimés')

                # 5. Supprimer les crédits
                count_credits = Credit.objects.count()
                Credit.objects.all().delete()
                self.stdout.write(f'✓ {count_credits} crédits supprimés')

                # 6. Supprimer les paiements (avant les RDV car foreign key)
                count_paiements = Paiement.objects.count()
                Paiement.objects.all().delete()
                self.stdout.write(f'✓ {count_paiements} paiements supprimés')

                # 7. Supprimer les options de RDV (cascade normalement, mais pour être sûr)
                count_rdv_options = RendezVousOption.objects.count()
                RendezVousOption.objects.all().delete()
                self.stdout.write(f'✓ {count_rdv_options} options de RDV supprimées')

                # 8. Supprimer les rendez-vous
                count_rdv = RendezVous.objects.count()
                RendezVous.objects.all().delete()
                self.stdout.write(f'✓ {count_rdv} rendez-vous supprimés')

                # 9. Supprimer les clôtures de caisse
                count_clotures = ClotureCaisse.objects.count()
                ClotureCaisse.objects.all().delete()
                self.stdout.write(f'✓ {count_clotures} clôtures de caisse supprimées')

                # 10. Supprimer les logs de modifications
                count_logs = ModificationLog.objects.count()
                ModificationLog.objects.all().delete()
                self.stdout.write(f'✓ {count_logs} logs de modifications supprimés')

                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('✅ Nettoyage terminé avec succès !'))
                self.stdout.write('')
                self.stdout.write('La base de données est maintenant propre et prête pour la production.')

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'❌ Erreur lors du nettoyage : {str(e)}'))
            self.stdout.write(self.style.ERROR('La transaction a été annulée, aucune donnée n\'a été supprimée.'))

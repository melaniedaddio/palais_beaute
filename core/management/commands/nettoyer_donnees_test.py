"""
Commande Django pour nettoyer toutes les données de test
et remettre la base de données dans un état propre pour la production.

Usage: python manage.py nettoyer_donnees_test
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import (
    RendezVous, RendezVousOption, GroupeRDV, Paiement, CarteCadeau,
    ForfaitClient, SeanceForfait, ModificationLog, ClotureCaisse,
    PaiementCredit, Credit,
    VenteProduit, LigneVenteProduit,
    Presence, ModificationPointage, Absence, Avertissement,
    CalculSalaire, Prime, Avance,
    MouvementStock, Produit,
    Inventaire, LigneInventaire,
    Depense, ValidationDepenseRecurrente,
    ReconciliationCaisse,
)


class Command(BaseCommand):
    help = 'Nettoie toutes les données de test (RDV, paiements, ventes, présences, salaires, stock, inventaires, dépenses)'

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
        self.stdout.write(f'  - Rendez-vous : {RendezVous.objects.count()} ({GroupeRDV.objects.count()} groupes)')
        self.stdout.write(f'  - Paiements : {Paiement.objects.count()}')
        self.stdout.write(f'  - Cartes cadeaux : {CarteCadeau.objects.count()}')
        self.stdout.write(f'  - Forfaits clients : {ForfaitClient.objects.count()}')
        self.stdout.write(f'  - Crédits : {Credit.objects.count()}')
        self.stdout.write(f'  - Clôtures de caisse : {ClotureCaisse.objects.count()}')
        self.stdout.write(f'  - Logs de modifications : {ModificationLog.objects.count()}')
        self.stdout.write(f'  - Ventes produits : {VenteProduit.objects.count()} ({LigneVenteProduit.objects.count()} lignes)')
        self.stdout.write(f'  - Présences : {Presence.objects.count()} ({ModificationPointage.objects.count()} modifications)')
        self.stdout.write(f'  - Absences : {Absence.objects.count()}')
        self.stdout.write(f'  - Avertissements : {Avertissement.objects.count()}')
        self.stdout.write(f'  - Salaires calculés : {CalculSalaire.objects.count()}')
        self.stdout.write(f'  - Primes : {Prime.objects.count()}')
        self.stdout.write(f'  - Avances : {Avance.objects.count()}')
        self.stdout.write(f'  - Mouvements de stock : {MouvementStock.objects.count()}')
        self.stdout.write(f'  - Inventaires : {Inventaire.objects.count()} ({LigneInventaire.objects.count()} lignes)')
        self.stdout.write(f'  - Dépenses : {Depense.objects.count()} ({ValidationDepenseRecurrente.objects.count()} validations récurrentes)')
        self.stdout.write(f'  - Réconciliations de caisse : {ReconciliationCaisse.objects.count()}')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Les données de configuration (instituts, employés, prestations, produits, clients) seront CONSERVÉES.'))
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

                # 8b. Supprimer les groupes de RDV (orphelins après suppression des RDV)
                count_groupes = GroupeRDV.objects.count()
                GroupeRDV.objects.all().delete()
                self.stdout.write(f'✓ {count_groupes} groupes de RDV supprimés')

                # 9. Supprimer les clôtures de caisse
                count_clotures = ClotureCaisse.objects.count()
                ClotureCaisse.objects.all().delete()
                self.stdout.write(f'✓ {count_clotures} clôtures de caisse supprimées')

                # 10. Supprimer les logs de modifications
                count_logs = ModificationLog.objects.count()
                ModificationLog.objects.all().delete()
                self.stdout.write(f'✓ {count_logs} logs de modifications supprimés')

                # 11. Ventes produits (lignes avant entêtes)
                count_lignes_vp = LigneVenteProduit.objects.count()
                LigneVenteProduit.objects.all().delete()
                self.stdout.write(f'✓ {count_lignes_vp} lignes de ventes produits supprimées')

                count_vp = VenteProduit.objects.count()
                VenteProduit.objects.all().delete()
                self.stdout.write(f'✓ {count_vp} ventes produits supprimées')

                # 12. Présences et audit trail
                count_modif_pt = ModificationPointage.objects.count()
                ModificationPointage.objects.all().delete()
                self.stdout.write(f'✓ {count_modif_pt} modifications de pointage supprimées')

                count_presences = Presence.objects.count()
                Presence.objects.all().delete()
                self.stdout.write(f'✓ {count_presences} présences supprimées')

                count_absences = Absence.objects.count()
                Absence.objects.all().delete()
                self.stdout.write(f'✓ {count_absences} absences supprimées')

                count_avert = Avertissement.objects.count()
                Avertissement.objects.all().delete()
                self.stdout.write(f'✓ {count_avert} avertissements supprimés')

                # 13. Salaires, primes, avances
                count_calculs = CalculSalaire.objects.count()
                CalculSalaire.objects.all().delete()
                self.stdout.write(f'✓ {count_calculs} calculs de salaire supprimés')

                count_primes = Prime.objects.count()
                Prime.objects.all().delete()
                self.stdout.write(f'✓ {count_primes} primes supprimées')

                count_avances = Avance.objects.count()
                Avance.objects.all().delete()
                self.stdout.write(f'✓ {count_avances} avances supprimées')

                # 14. Mouvements de stock + remise à zéro des stocks produits
                count_mvt = MouvementStock.objects.count()
                MouvementStock.objects.all().delete()
                self.stdout.write(f'✓ {count_mvt} mouvements de stock supprimés')
                count_produits = Produit.objects.update(stock_actuel=0)
                self.stdout.write(f'✓ {count_produits} produits remis à stock_actuel=0')

                # 15. Inventaires (lignes avant entêtes)
                count_lignes_inv = LigneInventaire.objects.count()
                LigneInventaire.objects.all().delete()
                self.stdout.write(f'✓ {count_lignes_inv} lignes d\'inventaire supprimées')

                count_inv = Inventaire.objects.count()
                Inventaire.objects.all().delete()
                self.stdout.write(f'✓ {count_inv} inventaires supprimés')

                # 16. Dépenses (validations récurrentes avant dépenses)
                count_valid_dep = ValidationDepenseRecurrente.objects.count()
                ValidationDepenseRecurrente.objects.all().delete()
                self.stdout.write(f'✓ {count_valid_dep} validations de dépenses récurrentes supprimées')

                count_dep = Depense.objects.count()
                Depense.objects.all().delete()
                self.stdout.write(f'✓ {count_dep} dépenses supprimées')

                # 17. Réconciliations de caisse
                count_reco = ReconciliationCaisse.objects.count()
                ReconciliationCaisse.objects.all().delete()
                self.stdout.write(f'✓ {count_reco} réconciliations de caisse supprimées')

                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('✅ Nettoyage terminé avec succès !'))
                self.stdout.write('')
                self.stdout.write('La base de données est maintenant propre et prête pour la production.')

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'❌ Erreur lors du nettoyage : {str(e)}'))
            self.stdout.write(self.style.ERROR('La transaction a été annulée, aucune donnée n\'a été supprimée.'))

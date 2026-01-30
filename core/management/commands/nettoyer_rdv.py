from django.core.management.base import BaseCommand
from core.models import (
    RendezVous, Paiement, Credit, PaiementCredit,
    ClotureCaisse, ModificationLog
)


class Command(BaseCommand):
    help = 'Nettoie tous les rendez-vous et données associées pour les tests'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("NETTOYAGE DES RENDEZ-VOUS ET DONNÉES ASSOCIÉES")
        self.stdout.write("=" * 60)

        # Compter avant suppression
        nb_rdv = RendezVous.objects.count()
        nb_paiements = Paiement.objects.count()
        nb_credits = Credit.objects.count()
        nb_paiements_credit = PaiementCredit.objects.count()
        nb_clotures = ClotureCaisse.objects.count()
        nb_logs = ModificationLog.objects.filter(rendez_vous__isnull=False).count()

        self.stdout.write("\nDonnées à supprimer:")
        self.stdout.write(f"  - Rendez-vous: {nb_rdv}")
        self.stdout.write(f"  - Paiements: {nb_paiements}")
        self.stdout.write(f"  - Crédits: {nb_credits}")
        self.stdout.write(f"  - Paiements de crédits: {nb_paiements_credit}")
        self.stdout.write(f"  - Clôtures de caisse: {nb_clotures}")
        self.stdout.write(f"  - Logs de modification: {nb_logs}")

        # Demander confirmation
        self.stdout.write("\n" + "=" * 60)
        confirmation = input("Êtes-vous sûr de vouloir tout supprimer? (oui/non): ")

        if confirmation.lower() != 'oui':
            self.stdout.write(self.style.WARNING('\nOpération annulée.'))
            return

        self.stdout.write("\nSuppression en cours...")

        # Supprimer dans l'ordre pour éviter les problèmes de clés étrangères

        # 1. Paiements de crédits
        self.stdout.write("\n[1/6] Suppression des paiements de crédits...")
        PaiementCredit.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"  ✓ {nb_paiements_credit} paiements de crédits supprimés"))

        # 2. Crédits
        self.stdout.write("\n[2/6] Suppression des crédits...")
        Credit.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"  ✓ {nb_credits} crédits supprimés"))

        # 3. Paiements
        self.stdout.write("\n[3/6] Suppression des paiements...")
        Paiement.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"  ✓ {nb_paiements} paiements supprimés"))

        # 4. Clôtures de caisse
        self.stdout.write("\n[4/6] Suppression des clôtures de caisse...")
        ClotureCaisse.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"  ✓ {nb_clotures} clôtures supprimées"))

        # 5. Logs de modification liés aux RDV
        self.stdout.write("\n[5/6] Suppression des logs de modification...")
        ModificationLog.objects.filter(rendez_vous__isnull=False).delete()
        self.stdout.write(self.style.SUCCESS(f"  ✓ {nb_logs} logs supprimés"))

        # 6. Rendez-vous
        self.stdout.write("\n[6/6] Suppression des rendez-vous...")
        RendezVous.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"  ✓ {nb_rdv} rendez-vous supprimés"))

        # Vérification finale
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("VÉRIFICATION FINALE")
        self.stdout.write("=" * 60)

        verif = {
            'Rendez-vous': RendezVous.objects.count(),
            'Paiements': Paiement.objects.count(),
            'Crédits': Credit.objects.count(),
            'Paiements de crédits': PaiementCredit.objects.count(),
            'Clôtures de caisse': ClotureCaisse.objects.count(),
            'Logs RDV': ModificationLog.objects.filter(rendez_vous__isnull=False).count()
        }

        all_zero = all(count == 0 for count in verif.values())

        for nom, count in verif.items():
            if count == 0:
                self.stdout.write(self.style.SUCCESS(f"  ✓ {nom}: 0"))
            else:
                self.stdout.write(self.style.ERROR(f"  ✗ {nom}: {count}"))

        if all_zero:
            self.stdout.write("\n" + self.style.SUCCESS("NETTOYAGE TERMINÉ AVEC SUCCÈS!"))
            self.stdout.write("\nLes données suivantes ont été conservées:")
            self.stdout.write("  ✓ Clients")
            self.stdout.write("  ✓ Employés")
            self.stdout.write("  ✓ Prestations")
            self.stdout.write("  ✓ Options")
            self.stdout.write("  ✓ Familles de prestations")
            self.stdout.write("  ✓ Instituts")
            self.stdout.write("  ✓ Utilisateurs")
            self.stdout.write("\nVous pouvez maintenant tester toutes les fonctionnalités!")
        else:
            self.stdout.write("\n" + self.style.WARNING("Attention: certaines données n'ont pas été supprimées."))

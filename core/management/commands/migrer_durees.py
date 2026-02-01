from django.core.management.base import BaseCommand
from core.models import Prestation
import re


class Command(BaseCommand):
    help = 'Migre les durées des prestations vers le format minutes'
    
    def handle(self, *args, **options):
        prestations = Prestation.objects.all()
        compteur_ok = 0
        compteur_erreur = 0
        
        for p in prestations:
            if p.duree and not p.duree_minutes:  # Si duree existe mais pas duree_minutes
                try:
                    # Convertir décimal en minutes
                    duree_heures = float(p.duree)
                    minutes = int(duree_heures * 60)
                    
                    if minutes > 0:
                        p.duree_minutes = minutes
                        p.save()
                        self.stdout.write(f"✓ {p.nom}: {duree_heures}h → {minutes} min")
                        compteur_ok += 1
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠ {p.nom}: durée = 0"))
                        compteur_erreur += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ {p.nom}: erreur - {str(e)}"))
                    compteur_erreur += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'\nMigration terminée: {compteur_ok} prestations migrées, {compteur_erreur} erreurs'
        ))

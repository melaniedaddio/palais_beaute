from django.core.management.base import BaseCommand
from core.models import Prestation


class Command(BaseCommand):
    help = 'Active toutes les prestations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--desactiver',
            action='store_true',
            help='Désactiver toutes les prestations au lieu de les activer'
        )

    def handle(self, *args, **options):
        desactiver = options.get('desactiver', False)

        if desactiver:
            # Désactiver toutes les prestations
            count = Prestation.objects.filter(actif=True).update(actif=False)
            self.stdout.write(
                self.style.SUCCESS(f'✅ {count} prestation(s) désactivée(s)')
            )
        else:
            # Activer toutes les prestations
            count = Prestation.objects.filter(actif=False).update(actif=True)
            self.stdout.write(
                self.style.SUCCESS(f'✅ {count} prestation(s) activée(s)')
            )

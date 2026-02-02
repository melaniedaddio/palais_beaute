"""
Script pour hasher les codes PIN existants dans la base de données.
À exécuter après la migration du modèle Utilisateur.
"""
from django.core.management.base import BaseCommand
from core.models import Utilisateur


class Command(BaseCommand):
    help = 'Hash les codes PIN existants en clair dans la base de données'

    def handle(self, *args, **options):
        # Récupérer tous les utilisateurs
        utilisateurs = Utilisateur.objects.all()

        if not utilisateurs.exists():
            self.stdout.write(
                self.style.WARNING('Aucun utilisateur trouvé')
            )
            return

        count_hashed = 0
        count_already_hashed = 0

        for utilisateur in utilisateurs:
            # Vérifier si le PIN est déjà hashé (commence par 'pbkdf2_sha256$')
            if utilisateur.pin.startswith('pbkdf2_sha256$') or utilisateur.pin.startswith('argon2'):
                count_already_hashed += 1
                self.stdout.write(
                    f'  - {utilisateur.user.username}: PIN déjà hashé'
                )
                continue

            # Le PIN est en clair, on le hash
            raw_pin = utilisateur.pin
            utilisateur.set_pin(raw_pin)
            utilisateur.save()
            count_hashed += 1

            self.stdout.write(
                self.style.SUCCESS(f'  - {utilisateur.user.username}: PIN hashé avec succès')
            )

        # Résumé
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'✅ {count_hashed} PIN(s) hashé(s)')
        )
        self.stdout.write(
            f'⏭️  {count_already_hashed} PIN(s) déjà hashé(s)'
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total: {utilisateurs.count()} utilisateur(s)')
        )

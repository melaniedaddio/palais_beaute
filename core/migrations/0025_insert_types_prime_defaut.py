from django.db import migrations


def creer_types_prime_defaut(apps, schema_editor):
    TypePrime = apps.get_model('core', 'TypePrime')
    types = [
        ('Meilleur chiffre manucuristes', 'Prime mensuelle pour la meilleure manucuriste'),
        ('Prime Jelly Spa', 'Prime liée aux prestations Jelly Spa'),
        ('Prime de rendement', 'Prime sur objectif de chiffre d\'affaires'),
        ('Prime d\'ancienneté', 'Prime liée à l\'ancienneté de l\'employé'),
    ]
    for nom, description in types:
        TypePrime.objects.get_or_create(nom=nom, defaults={'description': description})


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_add_salaires_models'),
    ]

    operations = [
        migrations.RunPython(creer_types_prime_defaut, reverse_func),
    ]

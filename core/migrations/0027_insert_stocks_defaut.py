from django.db import migrations


def creer_donnees_defaut(apps, schema_editor):
    CategorieProduit = apps.get_model('core', 'CategorieProduit')
    UniteMesure = apps.get_model('core', 'UniteMesure')

    categories = [
        ('Soins visage', 'Crèmes, sérums, masques visage'),
        ('Soins corps', 'Huiles, crèmes, gommages corps'),
        ('Ongles', 'Vernis, gels, accessoires manucure'),
        ('Cheveux', 'Shampoings, soins capillaires'),
        ('Consommables', 'Cotons, spatules, serviettes, etc.'),
        ('Matériel', 'Équipements et outils'),
    ]
    for nom, desc in categories:
        CategorieProduit.objects.get_or_create(nom=nom, defaults={'description': desc})

    unites = [
        ('Unité', 'u'),
        ('Flacon', 'fl'),
        ('Tube', 'tb'),
        ('Sachet', 'sac'),
        ('Boîte', 'bte'),
        ('Kilogramme', 'kg'),
        ('Litre', 'L'),
        ('Millilitre', 'ml'),
    ]
    for nom, abrv in unites:
        UniteMesure.objects.get_or_create(nom=nom, defaults={'abrv': abrv})


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_add_stocks_models'),
    ]

    operations = [
        migrations.RunPython(creer_donnees_defaut, reverse_func),
    ]

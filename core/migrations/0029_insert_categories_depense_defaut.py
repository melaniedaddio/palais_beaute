from django.db import migrations


def creer_categories_defaut(apps, schema_editor):
    CategoriDepense = apps.get_model('core', 'CategoriDepense')
    categories = [
        ('Loyer', 'Loyer mensuel des locaux'),
        ('Électricité', 'Factures électricité'),
        ('Eau', 'Factures eau'),
        ('Internet / Téléphone', 'Abonnements internet et téléphone'),
        ('Achats produits', 'Achats de produits et consommables'),
        ('Salaires', 'Paiement des salaires'),
        ('Entretien / Réparation', 'Entretien et réparation du matériel'),
        ('Transport', 'Frais de transport et livraison'),
        ('Publicité', 'Publicité et marketing'),
        ('Impôts / Taxes', 'Impôts, taxes et charges sociales'),
        ('Alimentation', 'Eau minérale, café, collations'),
        ('Autres', 'Autres dépenses diverses'),
    ]
    for nom, desc in categories:
        CategoriDepense.objects.get_or_create(nom=nom, defaults={'description': desc})


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_add_depenses_models'),
    ]

    operations = [
        migrations.RunPython(creer_categories_defaut, reverse_func),
    ]

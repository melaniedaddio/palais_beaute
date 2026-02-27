from django.db import migrations


def creer_types_absence_defaut(apps, schema_editor):
    TypeAbsence = apps.get_model('core', 'TypeAbsence')
    types = [
        ('Absence justifiée', True, 'Absence avec justificatif accepté'),
        ('Absence non justifiée', False, 'Absence sans justificatif'),
        ('Congé payé', True, 'Congé annuel payé'),
        ('Congé maladie', False, 'Maladie — payée uniquement si justificatif médical fourni'),
        ('Congé maternité', True, 'Congé maternité'),
        ('Permission', False, 'Permission accordée par le patron'),
        ('Mise à pied', False, 'Sanction disciplinaire'),
    ]
    for nom, est_payee, description in types:
        TypeAbsence.objects.get_or_create(
            nom=nom,
            defaults={'est_payee': est_payee, 'description': description}
        )


def supprimer_types_absence_defaut(apps, schema_editor):
    pass  # On ne supprime pas les données en cas de rollback


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_add_presences_models'),
    ]

    operations = [
        migrations.RunPython(creer_types_absence_defaut, supprimer_types_absence_defaut),
    ]

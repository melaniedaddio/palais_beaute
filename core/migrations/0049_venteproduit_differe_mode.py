from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0048_venteproduit_remise_pourcent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='venteproduit',
            name='mode_paiement',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('especes', 'Espèces'),
                    ('wave', 'Wave'),
                    ('om', 'Orange Money'),
                    ('carte', 'Carte bancaire'),
                    ('carte_cadeau', 'Carte cadeau'),
                    ('differe', 'Paiement différé'),
                ],
            ),
        ),
        migrations.AlterField(
            model_name='venteproduit',
            name='mode_paiement_2',
            field=models.CharField(
                max_length=20,
                blank=True,
                null=True,
                choices=[
                    ('especes', 'Espèces'),
                    ('wave', 'Wave'),
                    ('om', 'Orange Money'),
                    ('carte', 'Carte bancaire'),
                    ('carte_cadeau', 'Carte cadeau'),
                    ('differe', 'Paiement différé'),
                ],
            ),
        ),
    ]

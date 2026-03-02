from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_add_inventaire_depenses_recurrentes'),
    ]

    operations = [
        migrations.AddField(
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
                ],
            ),
        ),
        migrations.AddField(
            model_name='venteproduit',
            name='montant_paiement_1',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='venteproduit',
            name='montant_carte_utilise',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='venteproduit',
            name='carte_cadeau_utilisee',
            field=models.ForeignKey(
                to='core.CarteCadeau',
                on_delete=models.SET_NULL,
                null=True,
                blank=True,
                related_name='utilisations_ventes',
            ),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0034_vente_produit_double_paiement'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE core_categoridepense ADD COLUMN \"type\" VARCHAR(20) NOT NULL DEFAULT 'les_deux';",
            reverse_sql="ALTER TABLE core_categoridepense DROP COLUMN \"type\";",
            state_operations=[
                migrations.AddField(
                    model_name='CategoriDepense',
                    name='type',
                    field=models.CharField(
                        max_length=20,
                        choices=[
                            ('informelle', 'Informelle'),
                            ('recurrente', 'Récurrente'),
                            ('les_deux', 'Les deux'),
                        ],
                        default='les_deux',
                    ),
                ),
            ],
        ),
    ]

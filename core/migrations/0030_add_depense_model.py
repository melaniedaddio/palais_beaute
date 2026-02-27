from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    """Crée le modèle Depense (après insertion des catégories par défaut en 0029)."""

    dependencies = [
        ('core', '0029_insert_categories_depense_defaut'),
    ]

    operations = [
        migrations.CreateModel(
            name='Depense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('montant', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('date', models.DateField()),
                ('description', models.TextField(blank=True, null=True)),
                ('beneficiaire', models.CharField(blank=True, default='', max_length=200)),
                ('mode_paiement', models.CharField(
                    choices=[('especes', 'Espèces'), ('virement', 'Virement'), ('cheque', 'Chèque'),
                             ('carte', 'Carte bancaire'), ('om', 'Orange Money'), ('wave', 'Wave'), ('autre', 'Autre')],
                    default='especes', max_length=20
                )),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('categorie', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='depenses',
                    to='core.categoridepense'
                )),
                ('institut', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='depenses',
                    to='core.institut'
                )),
                ('cree_par', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='core.utilisateur'
                )),
            ],
            options={
                'verbose_name': 'Dépense',
                'verbose_name_plural': 'Dépenses',
                'ordering': ['-date', '-date_creation'],
            },
        ),
    ]

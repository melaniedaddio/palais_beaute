from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_insert_types_prime_defaut'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategorieProduit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Catégorie produit',
                'verbose_name_plural': 'Catégories produits',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='UniteMesure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=50, unique=True)),
                ('abrv', models.CharField(blank=True, default='', max_length=10)),
            ],
            options={
                'verbose_name': 'Unité de mesure',
                'verbose_name_plural': 'Unités de mesure',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='Fournisseur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('telephone', models.CharField(blank=True, default='', max_length=20)),
                ('email', models.EmailField(blank=True, default='')),
                ('actif', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Fournisseur',
                'verbose_name_plural': 'Fournisseurs',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='Produit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('reference', models.CharField(blank=True, default='', max_length=100)),
                ('prix_achat', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('stock_actuel', models.IntegerField(default=0)),
                ('stock_minimum', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('actif', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('categorie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='produits', to='core.categorieproduit')),
                ('unite', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='produits', to='core.unitemesure')),
                ('fournisseur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='produits', to='core.fournisseur')),
            ],
            options={
                'verbose_name': 'Produit',
                'verbose_name_plural': 'Produits',
                'ordering': ['categorie__nom', 'nom'],
            },
        ),
        migrations.CreateModel(
            name='MouvementStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_mouvement', models.CharField(choices=[('entree', 'Entrée'), ('sortie', 'Sortie'), ('inventaire', 'Inventaire'), ('perte', 'Perte/Casse')], max_length=20)),
                ('quantite', models.IntegerField()),
                ('quantite_avant', models.IntegerField(default=0)),
                ('quantite_apres', models.IntegerField(default=0)),
                ('prix_unitaire', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('commentaire', models.TextField(blank=True, null=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('produit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mouvements', to='core.produit')),
                ('cree_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.utilisateur')),
            ],
            options={
                'verbose_name': 'Mouvement de stock',
                'verbose_name_plural': 'Mouvements de stock',
                'ordering': ['-date_creation'],
            },
        ),
    ]

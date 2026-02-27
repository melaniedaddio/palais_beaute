from django.db import migrations, models


class Migration(migrations.Migration):
    """Crée uniquement CategoriDepense (Depense est créée dans 0030)."""

    dependencies = [
        ('core', '0027_insert_stocks_defaut'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoriDepense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Catégorie dépense',
                'verbose_name_plural': 'Catégories dépenses',
                'ordering': ['nom'],
            },
        ),
    ]

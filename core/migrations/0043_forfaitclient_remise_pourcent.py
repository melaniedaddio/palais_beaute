from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0042_mouvementstock_institut'),
    ]

    operations = [
        migrations.AddField(
            model_name='forfaitclient',
            name='remise_pourcent',
            field=models.IntegerField(
                default=0,
                help_text="Remise appliquée à l'achat (en %)",
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
    ]

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0049_venteproduit_differe_mode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paiementcredit',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]

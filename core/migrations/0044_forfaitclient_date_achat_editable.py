from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0043_forfaitclient_remise_pourcent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forfaitclient',
            name='date_achat',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0050_paiementcredit_date_editable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartecadeau',
            name='date_achat',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]

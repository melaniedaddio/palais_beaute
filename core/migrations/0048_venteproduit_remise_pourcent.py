from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0047_cartecadeau_hors_caisse'),
    ]

    operations = [
        migrations.AddField(
            model_name='venteproduit',
            name='remise_pourcent',
            field=models.IntegerField(default=0),
        ),
    ]

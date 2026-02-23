from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_client_date_naissance'),
    ]

    operations = [
        migrations.AddField(
            model_name='rendezvous',
            name='rappel_envoye',
            field=models.BooleanField(default=False),
        ),
    ]

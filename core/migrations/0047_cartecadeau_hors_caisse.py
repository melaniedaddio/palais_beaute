from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0046_add_notes_to_cartecadeau'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartecadeau',
            name='hors_caisse',
            field=models.BooleanField(
                default=False,
                help_text="Carte renseignée manuellement (non vendue en caisse) — exclue du CA"
            ),
        ),
    ]

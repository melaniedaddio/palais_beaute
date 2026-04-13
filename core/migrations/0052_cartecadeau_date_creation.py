from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_cartecadeau_date_achat_editable'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartecadeau',
            name='date_creation',
            field=models.DateTimeField(auto_now_add=True, null=True, help_text="Timestamp réel de création (pour le filtrage clôture)"),
            preserve_default=False,
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0041_inventaire_date_datetimefield'),
    ]

    operations = [
        migrations.AddField(
            model_name='mouvementstock',
            name='institut',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='mouvements_stock',
                to='core.institut',
            ),
        ),
    ]

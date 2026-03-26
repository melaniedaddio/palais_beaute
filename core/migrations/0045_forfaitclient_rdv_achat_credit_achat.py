from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_forfaitclient_date_achat_editable'),
    ]

    operations = [
        migrations.AddField(
            model_name='forfaitclient',
            name='rdv_achat',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='forfait_achat_set',
                to='core.rendezvous',
                help_text="RDV fictif créé lors de l'achat du forfait",
            ),
        ),
        migrations.AddField(
            model_name='forfaitclient',
            name='credit_achat',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='forfait_achat_set',
                to='core.credit',
                help_text="Crédit ouvert lors de l'achat du forfait (si paiement partiel)",
            ),
        ),
    ]

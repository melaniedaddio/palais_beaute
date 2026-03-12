from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_montant_retrait_cloture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventaire',
            name='date',
            field=models.DateTimeField(),
        ),
    ]

# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('megacellcnc', '0022_batteries_draft_json'),
    ]

    operations = [
        migrations.AddField(
            model_name='batteries',
            name='notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='batteries',
            name='pack_esr',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='batteries',
            name='manufacturing_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]

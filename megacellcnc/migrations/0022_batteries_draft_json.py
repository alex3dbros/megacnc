# Generated manually for pack draft support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('megacellcnc', '0021_remove_cells_bat_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='batteries',
            name='draft_json',
            field=models.JSONField(blank=True, null=True),
        ),
    ]

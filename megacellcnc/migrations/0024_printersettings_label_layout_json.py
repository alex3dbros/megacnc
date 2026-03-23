from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("megacellcnc", "0023_batteries_notes_pack_esr_mfg"),
    ]

    operations = [
        migrations.AddField(
            model_name="printersettings",
            name="CellLabelLayoutJson",
            field=models.TextField(blank=True, default="{}"),
        ),
        migrations.AddField(
            model_name="printersettings",
            name="BatteryLabelLayoutJson",
            field=models.TextField(blank=True, default="{}"),
        ),
    ]

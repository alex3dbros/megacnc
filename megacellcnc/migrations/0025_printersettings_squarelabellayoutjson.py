from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("megacellcnc", "0024_printersettings_label_layout_json"),
    ]

    operations = [
        migrations.AddField(
            model_name="printersettings",
            name="SquareLabelLayoutJson",
            field=models.TextField(blank=True, default="{}"),
        ),
    ]

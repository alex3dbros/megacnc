# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("megacellcnc", "0023_cells_condition"),
    ]

    operations = [
        migrations.CreateModel(
            name="BackupJournal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("action", models.CharField(max_length=64)),
                ("source", models.CharField(blank=True, max_length=500)),
                ("target", models.CharField(blank=True, max_length=500)),
                ("status", models.CharField(max_length=32)),
                ("detail", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]

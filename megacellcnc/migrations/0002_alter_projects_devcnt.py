# Generated by Django 5.0.2 on 2024-02-11 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('megacellcnc', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projects',
            name='DevCnt',
            field=models.IntegerField(default=0),
        ),
    ]

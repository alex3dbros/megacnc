# Seed MCCPro chemistry presets. Insert-only: never updates or deletes existing rows.

from django.db import migrations

PRESETS = (
    {
        "name": "Li-Ion",
        "max_voltage": 4.20,
        "min_voltage": 2.80,
        "store_Voltage": 3.70,
        "max_capacity": 5000,
        "chg_current": 2000,
        "pre_chg_current": 128,
        "ter_chg_current": 128,
        "discharge_current": 1000,
        "discharge_resistance": 1,
        "discharge_mod": 0,
        "max_temp": 45,
        "low_volt_max_time": 120,
        "max_charge_duration": 300,
        "discharge_cycles": 1,
    },
    {
        "name": "LiFePO4",
        "max_voltage": 3.65,
        "min_voltage": 2.50,
        "store_Voltage": 3.30,
        "max_capacity": 5000,
        "chg_current": 2000,
        "pre_chg_current": 128,
        "ter_chg_current": 128,
        "discharge_current": 1000,
        "discharge_resistance": 1,
        "discharge_mod": 0,
        "max_temp": 45,
        "low_volt_max_time": 120,
        "max_charge_duration": 300,
        "discharge_cycles": 1,
    },
    {
        "name": "LiPo",
        "max_voltage": 4.20,
        "min_voltage": 3.00,
        "store_Voltage": 3.80,
        "max_capacity": 5000,
        "chg_current": 2000,
        "pre_chg_current": 128,
        "ter_chg_current": 128,
        "discharge_current": 1000,
        "discharge_resistance": 1,
        "discharge_mod": 0,
        "max_temp": 45,
        "low_volt_max_time": 120,
        "max_charge_duration": 240,
        "discharge_cycles": 1,
    },
    {
        "name": "NMC",
        "max_voltage": 4.20,
        "min_voltage": 2.80,
        "store_Voltage": 3.70,
        "max_capacity": 5000,
        "chg_current": 2000,
        "pre_chg_current": 128,
        "ter_chg_current": 128,
        "discharge_current": 1000,
        "discharge_resistance": 1,
        "discharge_mod": 0,
        "max_temp": 45,
        "low_volt_max_time": 120,
        "max_charge_duration": 300,
        "discharge_cycles": 1,
    },
)


def seed_mccpro_chemistries(apps, schema_editor):
    Chemistry = apps.get_model("megacellcnc", "Chemistry")
    for preset in PRESETS:
        Chemistry.objects.get_or_create(
            device_type="MCCPro",
            name=preset["name"],
            defaults=preset,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("megacellcnc", "0024_backupjournal"),
    ]

    operations = [
        migrations.RunPython(seed_mccpro_chemistries, migrations.RunPython.noop),
    ]

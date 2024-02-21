# Generated by Django 5.0.2 on 2024-02-11 11:08

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cells',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UUID', models.CharField(max_length=150)),
                ('cell_type', models.CharField(max_length=150)),
                ('device_ip', models.GenericIPAddressField()),
                ('device_mac', models.CharField(max_length=150)),
                ('device_type', models.CharField(max_length=150)),
                ('device_slot', models.IntegerField()),
                ('voltage', models.FloatField()),
                ('capacity', models.FloatField()),
                ('esr', models.FloatField()),
                ('esr_ac', models.FloatField()),
                ('test_duration', models.FloatField()),
                ('charge_duration', models.FloatField()),
                ('discharge_duration', models.FloatField()),
                ('cycles_count', models.IntegerField()),
                ('temp_before_test', models.IntegerField()),
                ('avg_temp_charging', models.IntegerField()),
                ('avg_temp_discharging', models.IntegerField()),
                ('max_temp_charging', models.IntegerField()),
                ('max_temp_discharging', models.IntegerField()),
                ('min_voltage', models.FloatField()),
                ('max_voltage', models.FloatField()),
                ('store_voltage', models.FloatField()),
                ('testing_current', models.IntegerField()),
                ('discharge_mode', models.CharField(max_length=20)),
                ('status', models.CharField(max_length=150)),
                ('insertion_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('removal_date', models.DateTimeField()),
                ('available', models.CharField(max_length=150)),
            ],
        ),
        migrations.CreateModel(
            name='Chemistry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_type', models.CharField(max_length=150)),
                ('name', models.CharField(max_length=150)),
                ('max_voltage', models.FloatField()),
                ('min_voltage', models.FloatField()),
                ('store_Voltage', models.FloatField()),
                ('max_capacity', models.IntegerField()),
                ('chg_current', models.IntegerField()),
                ('pre_chg_current', models.IntegerField()),
                ('ter_chg_current', models.IntegerField()),
                ('discharge_current', models.IntegerField()),
                ('discharge_resistance', models.IntegerField()),
                ('discharge_mod', models.IntegerField()),
                ('max_temp', models.IntegerField()),
                ('low_volt_max_time', models.IntegerField()),
                ('max_charge_duration', models.IntegerField()),
                ('discharge_cycles', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Projects',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(max_length=150)),
                ('CreationDate', models.DateTimeField(default=django.utils.timezone.now)),
                ('CellType', models.CharField(max_length=150)),
                ('Notes', models.CharField(max_length=500)),
                ('LastCellNumber', models.IntegerField()),
                ('Status', models.CharField(default='Active', max_length=150)),
                ('TotalCells', models.IntegerField()),
                ('DevCnt', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='CellTestData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('voltage', models.FloatField()),
                ('current', models.FloatField()),
                ('capacity', models.FloatField()),
                ('status', models.CharField(max_length=50)),
                ('temperature', models.FloatField()),
                ('cycle_number', models.IntegerField()),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('cell', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_data', to='megacellcnc.cells')),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=150)),
                ('status', models.CharField(default='online', max_length=150)),
                ('name', models.CharField(max_length=150)),
                ('ip', models.GenericIPAddressField()),
                ('mac', models.CharField(max_length=255, unique=True)),
                ('insert_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('runtime', models.DurationField()),
                ('global_chemistry', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='megacellcnc.chemistry')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='devices', to='megacellcnc.projects')),
            ],
        ),
        migrations.AddField(
            model_name='cells',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='megacellcnc.projects'),
        ),
        migrations.CreateModel(
            name='Slot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slot_number', models.IntegerField()),
                ('voltage', models.FloatField(blank=True, null=True)),
                ('current', models.IntegerField(blank=True, null=True)),
                ('capacity', models.FloatField(blank=True, null=True)),
                ('charge_capacity', models.FloatField(blank=True, null=True)),
                ('state', models.CharField(blank=True, max_length=100, null=True)),
                ('esr', models.FloatField(blank=True, null=True)),
                ('action_running_time', models.FloatField(blank=True, null=True)),
                ('discharge_cycles_set', models.IntegerField(blank=True, null=True)),
                ('completed_cycles', models.IntegerField(blank=True, null=True)),
                ('temperature', models.FloatField(blank=True, null=True)),
                ('max_volt', models.FloatField(blank=True, null=True)),
                ('store_volt', models.FloatField(blank=True, null=True)),
                ('min_volt', models.FloatField(blank=True, null=True)),
                ('chemistry', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='slots', to='megacellcnc.chemistry')),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='megacellcnc.device')),
            ],
        ),
    ]

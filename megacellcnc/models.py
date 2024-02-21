from django.db import models
from django.utils import timezone


class Projects(models.Model):
    Name = models.CharField(max_length=150)
    CreationDate = models.DateTimeField(default=timezone.now)
    CellType = models.CharField(max_length=150)
    Notes = models.CharField(max_length=500)
    LastCellNumber = models.IntegerField()
    Status = models.CharField(max_length=150, default='Active')
    TotalCells = models.IntegerField()
    DevCnt = models.IntegerField(default=0)
    def __str__(self):
        return self.Name


class Cells(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    UUID = models.CharField(max_length=150)
    cell_type = models.CharField(max_length=150)
    device_ip = models.GenericIPAddressField()
    device_mac = models.CharField(max_length=150)
    device_type = models.CharField(max_length=150)
    device_slot = models.IntegerField()
    voltage = models.FloatField()
    capacity = models.FloatField()
    esr = models.FloatField()
    esr_ac = models.FloatField()
    test_duration = models.FloatField()
    charge_duration = models.FloatField()
    discharge_duration = models.FloatField()
    cycles_count = models.IntegerField()
    temp_before_test = models.IntegerField()
    avg_temp_charging = models.IntegerField()
    avg_temp_discharging = models.IntegerField()
    max_temp_charging = models.IntegerField()
    max_temp_discharging = models.IntegerField()
    min_voltage = models.FloatField()
    max_voltage = models.FloatField()
    store_voltage = models.FloatField()
    testing_current = models.IntegerField()
    discharge_mode = models.CharField(max_length=20) # on MCC PRO can have CC, CV, CR
    status = models.CharField(max_length=150)
    insertion_date = models.DateTimeField(default=timezone.now)
    removal_date = models.DateTimeField(null=True, blank=True)
    available = models.CharField(max_length=150)

    def __str__(self):
        return self.UUID


class CellTestData(models.Model):
    cell = models.ForeignKey(Cells, on_delete=models.CASCADE, related_name='test_data')
    voltage = models.FloatField()
    current = models.FloatField()
    capacity = models.FloatField()
    charging_capacity = models.FloatField()
    status = models.CharField(max_length=50)
    temperature = models.FloatField()
    cycle_number = models.IntegerField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.cell.UUID} - {self.timestamp}'


class Device(models.Model):
    type = models.CharField(max_length=150)
    status = models.CharField(max_length=150, default="online")
    name = models.CharField(max_length=150)
    ip = models.GenericIPAddressField()
    mac = models.CharField(max_length=255, unique=True)
    insert_date = models.DateTimeField(default=timezone.now)
    runtime = models.DurationField()
    discharge_mode = models.CharField(max_length=20, default="")
    discharge_current = models.IntegerField(default=0)
    cell_to_group = models.IntegerField(default=16)
    cell_per_group = models.IntegerField(default=1)

    project = models.ForeignKey('Projects', on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    global_chemistry = models.ForeignKey('Chemistry', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name




class Chemistry(models.Model):
    device_type = models.CharField(max_length=150)
    name = models.CharField(max_length=150)
    max_voltage = models.FloatField()
    min_voltage = models.FloatField()
    store_Voltage = models.FloatField()
    max_capacity = models.IntegerField()
    chg_current = models.IntegerField()
    pre_chg_current = models.IntegerField()
    ter_chg_current = models.IntegerField()
    discharge_current = models.IntegerField()
    discharge_resistance = models.IntegerField()
    discharge_mod = models.IntegerField()
    max_temp = models.IntegerField()
    low_volt_max_time = models.IntegerField()  # Low Voltage Recover Max Runtime in minutes
    max_charge_duration = models.IntegerField()  # in mins
    discharge_cycles = models.IntegerField()

    def __str__(self):
        return self.name


class Slot(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='slots')
    slot_number = models.IntegerField()  # To identify the slot within the device
    voltage = models.FloatField(null=True, blank=True)
    current = models.IntegerField(null=True, blank=True)
    capacity = models.FloatField(null=True, blank=True)
    charge_capacity = models.FloatField(null=True, blank=True)
    saved = models.BooleanField(default=False)
    active_cell = models.ForeignKey('Cells', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='active_in_slots')
    state = models.CharField(max_length=100, null=True, blank=True)
    esr = models.FloatField(null=True, blank=True)
    action_running_time = models.FloatField(null=True, blank=True) # Total runtime in seconds
    discharge_cycles_set = models.IntegerField(null=True, blank=True)
    completed_cycles = models.IntegerField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    max_volt = models.FloatField(null=True, blank=True)
    store_volt = models.FloatField(null=True, blank=True)
    min_volt = models.FloatField(null=True, blank=True)

    chemistry = models.ForeignKey(Chemistry, on_delete=models.SET_NULL, null=True, blank=True, related_name='slots')
    # Add any other fields that are relevant to the slot, such as status, voltage, etc.

    def __str__(self):
        return f"Slot {self.slot_number} of Device {self.device.name}"


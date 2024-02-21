from .models import Chemistry


def setUpTestData():
    # Set up non-modified objects used by all test methods
    Chemistry.objects.create(
        device_type='MCC',
        name='LifePo4',
        max_voltage=3.65,
        min_voltage=2.5,
        store_Voltage=3.3,
        max_capacity=250000,
        chg_current=1000,
        pre_chg_current=0,
        ter_chg_current=0,
        discharge_current=1000,
        discharge_resistance=0,
        discharge_mod=0,
        max_temp=45,
        low_volt_max_time=3600,
        max_charge_duration=5200,
        discharge_cycles=1
    )

setUpTestData()

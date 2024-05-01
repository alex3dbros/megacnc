from celery import shared_task, group
from megacellcnc.models import Device, Slot, Chemistry, CellTestData
from celery.exceptions import SoftTimeLimitExceeded
from mccprolib.api import MegacellCharger
from megacellcnc.functions import portscan, add_new_cell
import logging
from django.db import transaction
from django.core import serializers
from itertools import groupby
from operator import itemgetter
from django.db.models import Avg, Max
from django.utils import timezone

logger = logging.getLogger(__name__)


def constrain_value(min_allowed, max_allowed, actual_value):
    return max(min_allowed, min(max_allowed, actual_value))


def update_cell_data(device, slot):

    # Check if we should save this cell and generate serial
    if (slot.current > 50 or slot.current < -50) and not slot.saved:
        add_new_cell(device, slot)

    cell = slot.active_cell

    if cell:
        cell.voltage = slot.voltage
        cell.capacity = slot.capacity
        cell.esr = slot.esr
        if slot.state == "LVC Charging" or slot.state == "Started Charging":
            cell.charge_duration = slot.action_running_time

        if slot.state == "Started Discharging":
            if cell.charge_duration > 0 and slot.action_running_time > cell.charge_duration:
                cell.discharge_duration = slot.action_running_time - cell.charge_duration
            else:
                cell.discharge_duration = slot.action_running_time

        cell.cycles_count = slot.completed_cycles
        cell.min_voltage = slot.min_volt
        cell.max_voltage = slot.max_volt
        cell.store_voltage = slot.store_volt
        cell.testing_current = device.discharge_current
        cell.status = slot.state
        cell.test_duration = slot.action_running_time
        cell.save()

        record_states = ["LVC Charging", "Started Charging", "Cooldown", "Started Discharging", "ESR Reading", "Resting",
                         "Started Store Charging", "Started Store Discharging", "Dispose started", "mCap Started Charging",
                         "mCap Started Discharging", "mCap Store Charging", "mCap Store Discharging", "Wait For ESR Test",
                         "Cell rest 5 Min"]

        if slot.state in record_states:
            # Record data points
            new_data = CellTestData(
                cell=cell,
                voltage=slot.voltage,
                current=slot.current,
                capacity=slot.capacity,
                charging_capacity=slot.charge_capacity,
                status=slot.state,
                temperature=slot.temperature,
                cycle_number=slot.completed_cycles,
                timestamp=timezone.now()
            )
            new_data.save()


def cell_test_complete(cell):
    cell.removal_date = timezone.now()
    cell.status = "Removed"
    cell.available = "Yes"

    average_charge_temp_data = cell.test_data.filter(status='Started Charging').aggregate(Avg('temperature'))
    average_charge_temperature = average_charge_temp_data.get('temperature__avg')

    average_discharge_temp_data = cell.test_data.filter(status='Started Discharging').aggregate(Avg('temperature'))
    average_discharge_temperature = average_discharge_temp_data.get('temperature__avg')

    # Calculate the maximum temperature during charging
    max_temp_charging_data = cell.test_data.filter(status='Started Charging').aggregate(Max('temperature'))
    max_temp_charging = max_temp_charging_data.get('temperature__max')

    # Calculate the maximum temperature during discharging
    max_temp_discharging_data = cell.test_data.filter(status='Started Discharging').aggregate(Max('temperature'))
    max_temp_discharging = max_temp_discharging_data.get('temperature__max')

    cell.avg_temp_charging = average_charge_temperature
    cell.avg_temp_discharging = average_discharge_temperature
    cell.max_temp_charging = max_temp_charging
    cell.max_temp_discharging = max_temp_discharging

    cell.save()


def update_slot_data(device_model, tester, device_slot_count):
    slots = device_model.slots.all()
    current_slot_count = slots.count()

    # Updating slot count if it changed
    if current_slot_count != device_slot_count:
        # If different, delete all current slots and create new ones
        with transaction.atomic():  # Use a transaction to ensure atomicity
            # Delete all current slots
            slots.delete()

            # Create new slots
            for slot_num in range(1, device_slot_count + 1):  # Starting from 1 to slot_count
                Slot.objects.create(device=device_model, slot_number=slot_num)

        slots = device_model.slots.all()

    data = tester.get_cells_data()

    # First, sort the list of dictionaries by 'GiD'
    if "GiD" in data["cells"][0]:
        data_sorted = sorted(data["cells"], key=itemgetter('GiD'))

        # Then, group by 'GiD'
        groups = groupby(data_sorted, key=itemgetter('GiD'))
    else:
        data_sorted = sorted(data["cells"], key=itemgetter('CiD'))
        groups = groupby(data_sorted, key=itemgetter('CiD'))

    # To access the groups, you can iterate over them
    for gid, items in groups:
        slot_num = gid + 1
        cell = next(items)

        slot = device_model.slots.get(slot_number=slot_num)
        slot.voltage = cell["VlT"]
        slot.current = cell["AmP"]
        slot.capacity = cell["CaP"]
        slot.charge_capacity = cell["CCa"]
        slot.state = cell["StS"]

        if slot.saved and cell["StS"] == "Not Inserted":
            slot.saved = False
            if slot.active_cell:  # Check if there's an active cell
                cell_test_complete(slot.active_cell)

            slot.active_cell = None

        slot.esr = cell["esr"]
        slot.action_running_time = cell["AcL"]
        slot.discharge_cycles_set = cell["DiC"]
        slot.completed_cycles = cell["CoC"]
        slot.temperature = cell["TmP"]
        slot.max_volt = cell["MaV"]
        slot.store_volt = cell["StV"]
        slot.min_volt = cell["MiV"]
        slot.save()

        # Update the cell data and saved cell
        update_cell_data(device_model, slot)


@shared_task(soft_time_limit=10, time_limit=15)
def check_device_status(device_id):

    device = Device.objects.get(pk=device_id)

    res_dict = {}
    try:
        portscan(80, device.ip, res_dict)
        print(res_dict)
    except:
        pass

    if device.ip in res_dict:
        tester = MegacellCharger(device.ip)
        if tester.device_type and "ChT" in tester.device_type:
            device.status = "online"
            device.type = tester.device_type["ChT"]
            slot_count = tester.device_type["CeC"]
            device.save()

            update_slot_data(device, tester, slot_count)

            return True

        elif tester.device_type and 'McC' in tester.device_type:
            device.status = "online"
            device.type = "MCC"
            slot_count = tester.device_type["ByC"]
            device.save()
            update_slot_data(device, tester, slot_count)

            return True
    else:
        device.status = "offline"
        device.save()
        return False


@shared_task
def check_all_devices():
    devices = Device.objects.all()
    task_group = group(check_device_status.s(device.id) for device in devices)
    result_group = task_group.apply_async()
    return result_group


@shared_task
def dispatch_command(data, request_data, action_type):
    deviceId = data.get('deviceId')

    try:
        device = Device.objects.get(id=deviceId)
    # Now you can use 'device' object for further operations
    except Device.DoesNotExist:
        return "Fail"

    tester = MegacellCharger(device.ip)
    if action_type == "regular":
        result = tester.set_cells(request_data)
        return result

    elif action_type == "macro":
        result = tester.set_cells_macro(request_data)

        return result

    else:
        return False


@shared_task
def get_device_config(device_id):

    device = Device.objects.get(pk=device_id)

    res_dict = {}
    try:
        portscan(80, device.ip, res_dict)
        print(res_dict)
    except:
        pass

    if device.ip in res_dict:
        tester = MegacellCharger(device.ip)
        if tester.device_type and "ChT" in tester.device_type:

            if tester.device_type["ChT"] == "MCCPro":
                chems = Chemistry.objects.filter(device_type="MCCPro")
                mccpro_chemistries_json = serializers.serialize('json', chems)
                data = {"CiD": 0}
                device_conf = tester.get_cell_chemistry(data)
                return device_conf, mccpro_chemistries_json, tester.device_type["FwV"]

            elif tester.device_type["ChT"] == "MCCReg":
                chems = Chemistry.objects.filter(device_type="MCC")
                mcc_chemistries_json = serializers.serialize('json', chems)
                data = {"CiD": 0}
                device_conf = tester.get_cell_chemistry(data)

                return device_conf, mcc_chemistries_json, tester.device_type["FwV"]

        elif tester.device_type and 'McC' in tester.device_type:
            chems = Chemistry.objects.filter(device_type="MCC")
            mcc_chemistries_json = serializers.serialize('json', chems)
            device_conf = tester.get_config()

            return device_conf, mcc_chemistries_json, tester.device_type["McC"]
    else:
        return {}, {}


@shared_task
def save_device_config(device_id, data):

    device = Device.objects.get(pk=device_id)

    res_dict = {}
    try:
        portscan(80, device.ip, res_dict)
        print(res_dict)
    except:
        pass

    if device.ip in res_dict:
        tester = MegacellCharger(device.ip)


        maxVolt = constrain_value(3.5, 4.24, float(data["maxVoltage"]))
        minVolt = constrain_value(1.0, 4.0, float(data["minVoltage"]))
        sVolt = constrain_value(2.5, 4.24, float(data["storeVoltage"]))
        maxCap = constrain_value(100, 999999, int(data["maxCapacity"]))
        chgCur = constrain_value(500, 4500, int(data["chargingCurrent"]))
        pChgCur = constrain_value(128, 2048, int(data["prechargeCurrent"]))
        terChgCur = constrain_value(128, 2048, int(data["termChargingCurrent"]))
        dchgRes = constrain_value(1, 10, float(data["dischargeResistance"]))
        dchgMod = constrain_value(0, 2, int(data["dischargeMode"]))
        maxTemp = constrain_value(0, 55, int(data["maxTemp"]))
        LmR = constrain_value(5, 999999, int(data["maxLowVoltTime"]))
        McH = constrain_value(5, 999999, int(data["chargingTimeout"]))
        DiC = constrain_value(1, 999999, int(data["dischargeCycles"]))

        applyToSlot = constrain_value(1, 16, int(data["applyToSlot"]))

        cellsToGroup = constrain_value(1, 16, int(data["cellsToGroup"]))
        cellsPerGroup = constrain_value(1, 16, int(data["cellsPerGroup"]))
        tempSource = constrain_value(0, 1, int(data["tempSource"]))

        # Saving device data for display purposes
        device.name = data["deviceName"]
        device.discharge_mode = dchgMod
        device.discharge_current = int(data["dischargingCurrent"])
        device.cell_per_group = cellsPerGroup
        device.cell_to_group = cellsToGroup

        device.save()

        if tester.device_type and "ChT" in tester.device_type:

            if data["applyToAllSlots"] or tester.device_type["ChT"] == "MCCReg":
                print("I am applying chemistry to all slots")
                for slot in range(16):

                    chemistry = {
                        "Chem":
                            {
                                "id": 5,  # id's 1 to 4 are the ones shown on mcc menu, those cannot be modified
                                "name": "MegaCNC",
                                "maxVolt": maxVolt * 1000,
                                "minVolt": minVolt * 1000,
                                "sVolt": sVolt * 1000,
                                "maxCap": maxCap,
                                "chgCur": chgCur,
                                "pChgCur": pChgCur,
                                "terChgCur": terChgCur,
                                "dchgCur": constrain_value(100, 3000, int(data["dischargingCurrent"])),
                                "dchgRes": dchgRes,
                                "dchgMod": dchgMod,
                                "maxTemp": maxTemp,
                                "LmR": LmR,  # Low Voltage Recover Max Runtime in minutes
                                "McH": McH,  # Max charge duration in minutes
                                "DiC": DiC,  # Discharge cycles
                            },
                        "CiD": slot
                    }

                    tester.set_cell_chemistry(chemistry)


            else:

                chemistry = {
                    "Chem":
                        {
                            "id": 5,  # id's 1 to 4 are the ones shown on mcc menu, those cannot be modified
                            "name": "MegaCNC",
                            "maxVolt": maxVolt * 1000,
                            "minVolt": minVolt * 1000,
                            "sVolt": sVolt * 1000,
                            "maxCap": maxCap,
                            "chgCur": chgCur,
                            "pChgCur": pChgCur,
                            "terChgCur": terChgCur,
                            "dchgCur": constrain_value(100, 3000, int(data["dischargingCurrent"])),
                            "dchgRes": dchgRes,
                            "dchgMod": dchgMod,
                            "maxTemp": maxTemp,
                            "LmR": LmR,  # Low Voltage Recover Max Runtime in minutes
                            "McH": McH,  # Max charge duration in minutes
                            "DiC": DiC,  # Discharge cycles

                        },
                    "CiD": applyToSlot - 1
                }
                tester.set_cell_chemistry(chemistry)
                print("I am applying chemistry to one slot %s" % (int(data["applyToSlot"]) - 1))

            # Setting the hardware config
            tester.set_hardware_config(tempSource, cellsToGroup, cellsPerGroup, 0)
            print("This is data from task")
            print(data)
            return True

        elif tester.device_type and 'McC' in tester.device_type:
            config = {
                "ChC": True,
                "MaV": maxVolt,
                "StV": sVolt,
                "MiV": minVolt,
                "MaT": maxTemp,
                "DiC": DiC,
                "LmV": 0.3,
                "LcV": 3.6,
                "LmD": 1.1, # Limit volt drop
                "LmR": 500,
                "McH": int(data["chargingTimeout"]),
                "LcR": 200,
                "MsR": 2000,
                "DiR": constrain_value(100, 990, int(data["dischargingCurrent"])),
                "CcO": 1,
                "DcO": 1
                    }

            tester.set_config(config)

            return True
    else:
        return False

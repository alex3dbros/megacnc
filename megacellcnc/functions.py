import time
from threading import Thread
import socket
import netaddr
import re
from mccprolib.api import MegacellCharger
from .models import Projects, Cells
import re
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.utils import timezone

def extract_segment(host):
    # Define a regex pattern to capture the segment between the first hyphen and the first dot
    pattern = r'-([^.]+)\.'

    # Search for the pattern in the provided hostname
    match = re.search(pattern, host)

    # If a match is found, return the captured group, otherwise return None or an appropriate default value
    return match.group(1) if match else None


def portscan(port, host, res_dict):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)#

    try:
        con = s.connect((host, port))
        hostname = socket.gethostbyaddr(host)
        # print("Port %s, is open for: %s, hostname: %s" % (port, host, hostname[0]))
        res_dict[host] = hostname[0]
        con.close()
    except:
        pass


def scan_ip_range(startIP, endIP):
    results = {}
    threads = list()
    iprange = netaddr.ip.IPRange(startIP, endIP)

    for ip in iprange:
        host = str(ip)
        t = Thread(target=portscan, args=(80, host, results))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # for k in results:
    #     print("This is IP: %s, this is Hostname: %s" % (k, results[k]))

    return results


def scan_for_devices(from_ip, to_ip):

    devices = scan_ip_range(from_ip, to_ip)
    devices_list = []
    dev_id = 0
    for ip, hostname in devices.items():
        print(ip, hostname)

        if "ESP-" in hostname:
            device_name = extract_segment(hostname)
            print(device_name)
            tester_info = {}
            tester_type = ""
            mac_address = ""
            slot_count = 0
            firmware_v = ""
            try:
                tester = MegacellCharger(ip)
                tester_info = tester.get_device_type()
                print(tester_info)
            except:
                continue

            if 'ChT' in tester_info:
                tester_type = tester_info["ChT"]
                mac_address = tester_info["McA"]
                slot_count = tester_info["CeC"]
                firmware_v = tester_info["FwV"]
            elif 'McC' in tester_info:
                tester_type = "MCC"
                mac_address = tester_info["McA"]
                slot_count = tester_info["ByC"]
                firmware_v = tester_info["McC"]
            else:
                tester_type = "Unknown"

            devices_list.append({'id': dev_id, 'name': device_name, 'ip': ip, 'type': tester_type, 'mac': mac_address, 'slot_count': slot_count,
                                 'firmware_version': firmware_v})
            dev_id += 1


    return devices_list


def generate_uuid_for_cell(project_id):
    # Query the last cell for the given project ID, ordered by ID to get the most recent one
    last_cell = Cells.objects.filter(project_id=project_id).order_by('-id').first()

    if last_cell:
        # Extract the serial number from the last cell's UUID
        match = re.search(r'-S(\d+)', last_cell.UUID)
        if match:
            serial_number = int(match.group(1)) + 1  # Increment the serial number
        else:
            # If for some reason the UUID format is wrong, start a new serial number
            serial_number = 1
    else:
        # If there are no cells for the project, start with serial number 1
        serial_number = 1

    # Generate a new UUID using today's date and the new serial number
    date_prefix = datetime.now().strftime('D%Y%m%d')
    new_uuid = f"{date_prefix}-S{serial_number:06d}"  # Assuming a fixed capacity part for simplicity

    return new_uuid


def add_new_cell(device, slot):
    project_instance = get_object_or_404(Projects, id=device.project_id)
    uuid = generate_uuid_for_cell(device.project_id)

    # Create and save the new cell
    new_cell = Cells(
        project=project_instance,
        UUID=uuid,
        cell_type=project_instance.CellType,
        device_ip=device.ip,
        device_mac=device.mac,
        device_type=device.type,
        device_slot=slot.slot_number,
        voltage=slot.voltage,
        capacity=slot.capacity,
        esr=slot.esr,
        esr_ac=0,
        test_duration=slot.action_running_time,
        charge_duration=0,
        discharge_duration=0,
        cycles_count=slot.completed_cycles,
        temp_before_test=slot.temperature,
        avg_temp_charging=0,
        avg_temp_discharging=0,
        max_temp_charging=0,
        max_temp_discharging=0,
        min_voltage=slot.min_volt,
        max_voltage=slot.max_volt,
        store_voltage=slot.store_volt,
        testing_current=device.discharge_current,
        discharge_mode=device.discharge_mode,
        status=slot.state,
        insertion_date=timezone.now(),
        available='No'
    )
    new_cell.save()

    # Update the slot
    slot.saved = True
    slot.active_cell = new_cell
    slot.save()

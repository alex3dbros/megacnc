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
from PIL import Image, ImageFont, ImageDraw
import os
from django.conf import settings as main_settings
import qrcode
import base64
from io import BytesIO
import ipaddress

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


def is_valid_ip(manual_ip):
    try:
        ipaddress.ip_address(manual_ip)
        return True
    except ValueError:
        return False


def scan_for_devices(from_ip, to_ip, manual_ip):

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

    if manual_ip != "" and is_valid_ip(manual_ip):
        tester_info = {}
        tester_type = ""
        mac_address = ""
        slot_count = 0
        firmware_v = ""


        try:
            tester = MegacellCharger(manual_ip)
            tester_info = tester.get_device_type()
            print(tester_info)

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

            # Check if the new IP address is already in the list of dictionaries
            if any(d['ip'] == manual_ip for d in devices_list):
                pass
            else:
                devices_list.append({'id': dev_id, 'name': mac_address, 'ip': manual_ip, 'type': tester_type, 'mac': mac_address, 'slot_count': slot_count,
                                     'firmware_version': firmware_v})

        except:
            print("Could not connect to manual ip device")

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


def format_cap(capacity):

    # Check if capacity is greater than 9999 mAh
    if capacity > 9999:
        # Convert to Ah and format the value
        cap = round(capacity / 1000.0, 2)
        capUnit = "Ah"
    else:
        capUnit = "mAh"
        cap = int(capacity)

    return cap, capUnit


def draw_dual_label(label_data):

    if len(label_data) == 0:
        label_data = [{"serial": 1, "uuid": "D20240219-S000001", "cap": 32450, "esr": 0.1, "temp": 25, "minV": 2.8, "storeV": 3.7, "maxV": 4.24,
                       "ip": "192.168.1.104", "slot": 1},
                      {"serial": 2, "uuid": "D20240219-S000002", "cap": 3200, "esr": 0.12, "temp": 24, "minV": 2.8, "storeV": 3.7, "maxV": 4.24,
                       "ip": "192.168.1.104", "slot": 2}]

    templates_folder = os.path.join(main_settings.BASE_DIR, 'static', 'labeltemplates')
    dymo_label_location = os.path.join(templates_folder, 'dymo_blank_13x25.jpg')
    preview_location = os.path.join(templates_folder, 'preview.jpg')
    header_font_location = os.path.join(templates_folder, 'fonts', 'OpenSans-Bold.ttf')
    left_values_font_loc = os.path.join(templates_folder, 'fonts', 'OpenSans-Regular.ttf')

    label = Image.open(dymo_label_location)
    header_font = ImageFont.truetype(header_font_location, 62)
    left_values_font = ImageFont.truetype(left_values_font_loc, 42)

    label_editable = ImageDraw.Draw(label)

    offset = 0

    for l in label_data:

        capacity, unit = format_cap(l["cap"])
        serial = str(l["serial"]).zfill(6)
        header_text = "%s-C:%s" % (serial, capacity)
        label_editable.text((40, offset + -20), header_text, (0, 0, 0), font=header_font)

        first_row = "I:%s T:%s" % (l["esr"], l["temp"])
        label_editable.text((40, offset + 50), first_row, (0, 0, 0), font=left_values_font)

        second_row = "%s/%s/%s" % (l["minV"], l["storeV"], l["maxV"])
        label_editable.text((40, offset + 100), second_row, (0, 0, 0), font=left_values_font)

        last_ip_num = l["ip"].split(".")[-1]
        third_row = "Mc: %s-%s" % (last_ip_num, l["slot"])
        label_editable.text((40, offset + 150), third_row, (0, 0, 0), font=left_values_font)

        # Adding the unit
        text_image = Image.new('RGBA', (100, 100), (255, 255, 255, 0))  # Adjust size as needed
        draw = ImageDraw.Draw(text_image)

        draw.text((0, 0), unit, (0, 0, 0), font=left_values_font)
        rotated_text_image = text_image.rotate(-90, expand=1, fillcolor=(255, 255, 255, 0))

        label.paste(rotated_text_image, (250, offset + 80), rotated_text_image)

        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=5)

        qr.add_data("%s-C%s-%s" % (l["uuid"], capacity, unit))
        qr.make(fit=True)
        qr_img = qr.make_image(fill='black', back_color='white')
        qr_img = qr_img.crop((0, 0, 350, 350))
        qr_img = qr_img.resize((170, 170))

        label.paste(qr_img, (340, offset + 50))

        offset += 240

    label = label.rotate(90)

    buffered = BytesIO()
    label.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    buffered.seek(0)

    with open(preview_location, 'wb') as f:
        f.write(buffered.getvalue())

    return img_str



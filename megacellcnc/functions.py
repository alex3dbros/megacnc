import time
from threading import Thread
import socket
import netaddr
import re
from mccprolib.api import MegacellCharger
from .models import Projects, Cells, Device, Batteries
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
import json
import logging
import msgpack

logger = logging.getLogger(__name__)

def extract_segment(host):
    # Define a regex pattern to capture the segment between the first hyphen and the first dot
    pattern = r'-([^.]+)\.'

    # Search for the pattern in the provided hostname
    match = re.search(pattern, host)

    # If a match is found, return the captured group, otherwise return None or an appropriate default value
    return match.group(1) if match else None


SCAN_PORT_TIMEOUT = 2
SCAN_HTTP_TIMEOUT = 8
SCAN_BATCH_SIZE = 48


def portscan(port, host, res_dict, timeout=1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((host, port))
    if result == 0:
        res_dict[host] = result
    sock.close()


def scan_ip_range(startIP, endIP):
    """Find hosts with port 80 open (batched portscan, then HTTP only for hits)."""
    results = {}
    hosts = [str(ip) for ip in netaddr.ip.IPRange(startIP, endIP)]

    for i in range(0, len(hosts), SCAN_BATCH_SIZE):
        threads = []
        for host in hosts[i:i + SCAN_BATCH_SIZE]:
            t = Thread(target=portscan, args=(80, host, results, SCAN_PORT_TIMEOUT))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

    return results


def _read_charger_identity(ip, timeout=SCAN_HTTP_TIMEOUT):
    info = MegacellCharger.probe_device(ip, timeout=timeout)
    if info:
        return info
    try:
        tester = MegacellCharger(ip)
        if tester.device_type and tester.device_type != "Unknown":
            return tester.device_type
    except Exception:
        pass
    return None


def _device_entry_from_identity(tester_info, ip, dev_id):
    if not tester_info or not isinstance(tester_info, dict):
        return None

    if 'ChT' in tester_info:
        tester_type = tester_info["ChT"]
        mac_address = tester_info.get("McA", "")
        slot_count = tester_info.get("CeC", 0)
        firmware_v = tester_info.get("FwV", "")
    elif 'McC' in tester_info:
        tester_type = "MCC"
        mac_address = tester_info.get("McA", "")
        slot_count = tester_info.get("ByC", 0)
        firmware_v = tester_info["McC"]
    else:
        return None

    if not mac_address:
        return None

    last_three_parts = mac_address.split(":")[-3:]
    device_name = tester_type + "-" + "".join(last_three_parts)
    return {
        'id': dev_id,
        'name': device_name,
        'ip': ip,
        'type': tester_type,
        'mac': mac_address,
        'slot_count': slot_count,
        'firmware_version': firmware_v,
    }


def is_valid_ip(manual_ip):
    try:
        ipaddress.ip_address(manual_ip)
        return True
    except ValueError:
        return False


def scan_for_devices(from_ip, to_ip, manual_ip):

    open_hosts = scan_ip_range(from_ip, to_ip)
    devices_list = []
    dev_id = 0
    seen_ips = set()

    for ip in sorted(open_hosts.keys()):
        entry = _device_entry_from_identity(_read_charger_identity(ip), ip, dev_id)
        if entry:
            devices_list.append(entry)
            seen_ips.add(ip)
            dev_id += 1

    if manual_ip and is_valid_ip(manual_ip) and manual_ip not in seen_ips:
        entry = _device_entry_from_identity(_read_charger_identity(manual_ip), manual_ip, dev_id)
        if entry:
            devices_list.append(entry)

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
    project_instance.update_total_cells()
    # Update the slot
    slot.saved = True
    slot.active_cell = new_cell
    slot.save()


def _chem_field(chem, *keys, default=0):
    """Read chemistry field from dict (supports API key variants)."""
    if not isinstance(chem, dict):
        return default
    for key in keys:
        if key in chem and chem[key] is not None:
            return chem[key]
    return default


def normalize_mccpro_chemistry_payload(raw):
    """
    Decode MCCPro/MCCReg get_chemistry response (msgpack bytes, list, or dict).
    Returns a dict with Chem fields or a legacy numeric list.
    """
    if raw is None:
        return None
    if isinstance(raw, str):
        try:
            return normalize_mccpro_chemistry_payload(json.loads(raw))
        except Exception:
            pass
        try:
            return normalize_mccpro_chemistry_payload(raw.encode('latin-1'))
        except Exception:
            pass
        logger.warning("normalize_mccpro_chemistry_payload: unparseable str len=%s", len(raw))
        return None
    if isinstance(raw, dict):
        if 'kombu.bytes' in raw:
            try:
                return normalize_mccpro_chemistry_payload(base64.b64decode(raw['kombu.bytes']))
            except Exception:
                pass
        chem = raw.get('Chem')
        if isinstance(chem, dict):
            return chem
        if chem is not None:
            return normalize_mccpro_chemistry_payload(chem)
        if any(k in raw for k in ('maxVolt', 'minVolt', 'maxCap', 'chgCur')):
            return raw
        return raw.get('Chem', raw) if 'Chem' in raw else None
    if isinstance(raw, (list, tuple)):
        if len(raw) == 0:
            return None
        item = raw[-1] if len(raw) > 1 else raw[0]
        if isinstance(item, dict):
            return item.get('Chem', item)
        return item
    if isinstance(raw, bytes):
        try:
            unpacker = msgpack.Unpacker(raw=False, strict_map_key=False)
            unpacker.feed(raw)
            items = list(unpacker)
            if items:
                return normalize_mccpro_chemistry_payload(
                    items[-1] if len(items) > 1 else items[0]
                )
        except Exception:
            pass
        try:
            unpacked = msgpack.unpackb(raw, raw=False, strict_map_key=False)
            return normalize_mccpro_chemistry_payload(unpacked)
        except Exception:
            pass
        try:
            text = raw.decode('utf-8').strip()
            if text:
                return normalize_mccpro_chemistry_payload(json.loads(text))
        except Exception:
            pass
    return None


def build_mccpro_edit_device_data(dev_data, device, slots_count, chems, firmware_version):
    """Map live MCCPro chemistry to edit_device JSON (dict or legacy array)."""
    if isinstance(dev_data, dict):
        c = dev_data.get('Chem', dev_data)
        return {
            "dev_type": device.type,
            "max_charge_volt": round(float(_chem_field(c, 'maxVolt', 'max_voltage')) / 1000, 2),
            "store_volt": round(float(_chem_field(c, 'sVolt', 'store_Voltage', 'store_volt')) / 1000, 2),
            "discharge_volt": round(float(_chem_field(c, 'minVolt', 'min_voltage')) / 1000, 2),
            "max_temp": round(float(_chem_field(c, 'maxTemp', 'max_temp')), 2),
            "discharge_cycles": int(_chem_field(c, 'DiC', 'discharge_cycles')),
            "firmware": firmware_version,
            "discharge_current": int(_chem_field(c, 'dchgCur', 'discharge_current')),
            "charging_current": int(_chem_field(c, 'chgCur', 'chg_current')),
            "charging_timeout": int(_chem_field(c, 'McH', 'max_charge_duration')),
            "device_name": device.name,
            "slots_count": slots_count,
            "chems": chems,
            "max_capacity": int(_chem_field(c, 'maxCap', 'max_capacity')),
            "pre_charge_current": int(_chem_field(c, 'pChgCur', 'pre_chg_current')),
            "term_charging_current": int(_chem_field(c, 'terChgCur', 'ter_chg_current')),
            "discharge_resistance": float(_chem_field(c, 'dchgRes', 'discharge_resistance')),
            "discharge_mode": int(_chem_field(c, 'dchgMod', 'discharge_mod')),
            "max_low_volt_recovery_time": int(_chem_field(c, 'LmR', 'low_volt_max_time')),
            "chemistry_id": int(_chem_field(c, 'id', default=5)),
            "cells_to_group": device.cell_to_group,
            "cells_per_group": device.cell_per_group,
        }
    if isinstance(dev_data, (list, tuple)) and len(dev_data) >= 16:
        return {
            "dev_type": device.type,
            "max_charge_volt": round(dev_data[2] / 1000, 2),
            "store_volt": round(dev_data[4] / 1000, 2),
            "discharge_volt": round(dev_data[3] / 1000, 2),
            "max_temp": round(dev_data[12], 2),
            "discharge_cycles": dev_data[15],
            "firmware": firmware_version,
            "discharge_current": int(dev_data[9]),
            "charging_current": dev_data[6],
            "charging_timeout": dev_data[14],
            "device_name": device.name,
            "slots_count": slots_count,
            "chems": chems,
            "max_capacity": dev_data[5],
            "pre_charge_current": dev_data[7],
            "term_charging_current": dev_data[8],
            "discharge_resistance": dev_data[10],
            "discharge_mode": dev_data[11],
            "max_low_volt_recovery_time": dev_data[13],
            "chemistry_id": int(dev_data[0]) if len(dev_data) > 0 else 5,
            "cells_to_group": device.cell_to_group,
            "cells_per_group": device.cell_per_group,
        }
    raise ValueError(f'Unbekanntes Chemistry-Format: {type(dev_data).__name__}')


def is_charger_api_error(raw):
    if raw is None:
        return True
    if isinstance(raw, bytes):
        text = raw.decode('utf-8', errors='replace').strip().lower()
        if not text:
            return True
        return 'not found' in text or 'file not found' in text or text.startswith('error')
    if isinstance(raw, str):
        text = raw.strip().lower()
        return 'not found' in text or text.startswith('error')
    return False


def _volt_to_mv(value, default=0):
    if value is None:
        return default
    v = float(value)
    return int(round(v * 1000)) if v < 10 else int(round(v))


def _device_discharge_mode(device):
    if not device or not device.discharge_mode:
        return 0
    try:
        return int(device.discharge_mode)
    except (TypeError, ValueError):
        return 0


def chemistry_dict_from_cell(cell, device=None):
    dchg = device.discharge_current if device and device.discharge_current else None
    return {
        "id": 5,
        "maxVolt": _volt_to_mv(cell.get("MaV"), 4200),
        "minVolt": _volt_to_mv(cell.get("MiV"), 2800),
        "sVolt": _volt_to_mv(cell.get("StV"), 3700),
        "DiC": int(cell.get("DiC") or 1),
        "maxTemp": int(cell.get("TmP") or cell.get("MaT") or 35),
        "dchgCur": int(dchg or cell.get("DiR") or cell.get("dchgCur") or 500),
        "chgCur": int(cell.get("ChgC") or cell.get("chgCur") or 2000),
        "pChgCur": int(cell.get("pChgCur") or 128),
        "terChgCur": int(cell.get("terChgCur") or 128),
        "dchgRes": float(cell.get("dchgRes") or 1),
        "dchgMod": _device_discharge_mode(device) or int(cell.get("dchgMod") or 0),
        "maxCap": int(cell.get("maxCap") or cell.get("CaP") or 4500),
        "McH": int(cell.get("McH") or 300),
        "LmR": int(cell.get("LmR") or 120),
    }


def chemistry_dict_from_db(device, slot=None):
    from megacellcnc.models import Chemistry

    if slot and slot.max_volt:
        return chemistry_dict_from_cell({
            "MaV": slot.max_volt,
            "MiV": slot.min_volt,
            "StV": slot.store_volt,
            "DiC": slot.discharge_cycles_set or 1,
        }, device)

    preset = device.global_chemistry or Chemistry.objects.filter(device_type="MCCPro").first()
    if preset:
        return {
            "id": 5,
            "maxVolt": _volt_to_mv(preset.max_voltage),
            "minVolt": _volt_to_mv(preset.min_voltage),
            "sVolt": _volt_to_mv(preset.store_Voltage),
            "DiC": int(preset.discharge_cycles),
            "maxTemp": int(preset.max_temp),
            "dchgCur": int(device.discharge_current or preset.discharge_current),
            "chgCur": int(preset.chg_current),
            "pChgCur": int(preset.pre_chg_current),
            "terChgCur": int(preset.ter_chg_current),
            "dchgRes": float(preset.discharge_resistance),
            "dchgMod": _device_discharge_mode(device) or int(preset.discharge_mod),
            "maxCap": int(preset.max_capacity),
            "McH": int(preset.max_charge_duration),
            "LmR": int(preset.low_volt_max_time),
        }
    return chemistry_dict_from_cell({}, device)


def fetch_mccpro_chemistry(tester, device, cid=0):
    """
    Read MCCPro chemistry from device API; fall back to live cells, cached slots, or DB.
    Returns (chem_dict, source) where source is device|cells|slots|database.
    """
    raw = tester.get_cell_chemistry({"CiD": cid})
    if raw is not None and not is_charger_api_error(raw):
        parsed = normalize_mccpro_chemistry_payload(raw)
        if parsed is not None:
            if isinstance(parsed, dict) and 'Chem' in parsed:
                parsed = parsed['Chem']
            return parsed, "device"

    slot_num = cid + 1
    try:
        info = tester.get_data({"start": slot_num, "end": slot_num}, "api/get_cells_info")
        cells = info.get("cells") or []
        if cells:
            return chemistry_dict_from_cell(cells[0], device), "cells"
    except Exception as e:
        logger.warning("get_cells_info fallback failed for %s: %s", device.ip, e)

    slot = device.slots.filter(slot_number=slot_num).first()
    if slot and slot.max_volt:
        return chemistry_dict_from_db(device, slot), "slots"

    return chemistry_dict_from_db(device), "database"


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
        label_data = [{"serial": "000001", "uuid": "D20240219-S000001", "cap": 32450,
                       "ip": "192.168.1.104", "slot": 1, "date": "2024-02-19"},
                      {"serial": "000002", "uuid": "D20240219-S000002", "cap": 3200,
                       "ip": "192.168.1.104", "slot": 2, "date": "2024-02-19"}]

    templates_folder = os.path.join(main_settings.BASE_DIR, 'static', 'labeltemplates')
    dymo_label_location = os.path.join(templates_folder, 'dymo_blank_13x25.jpg')
    preview_location = os.path.join(templates_folder, 'preview.jpg')
    header_font_location = os.path.join(templates_folder, 'fonts', 'OpenSans-Bold.ttf')
    left_values_font_loc = os.path.join(templates_folder, 'fonts', 'OpenSans-Regular.ttf')

    label = Image.open(dymo_label_location)
    header_font = ImageFont.truetype(header_font_location, 62)
    left_values_font = ImageFont.truetype(left_values_font_loc, 42)
    brand_font2 = ImageFont.truetype(left_values_font_loc, 32)

    label_editable = ImageDraw.Draw(label)

    offset = 0

    for l in label_data:

        capacity, unit = format_cap(l["cap"])

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data("%s-C%s-%s" % (l["uuid"], capacity, unit))
        qr.make(fit=True)
        qr_img = qr.make_image(fill='black', back_color='white')
        qr_img = qr_img.crop((0, 0, 350, 350))
        qr_img = qr_img.resize((220, 220))
        label.paste(qr_img, (300, offset + 30))

        serial = str(l["serial"])
        header_text = "%s-C:%s" % (serial, capacity)
        label_editable.text((10, offset + -20), header_text, (0, 0, 0), font=header_font)

        last_ip_num = l["ip"].split(".")[-1]
        third_row = "Mc: %s-%s" % (last_ip_num, l["slot"])
        label_editable.text((10, offset + 40), third_row, (0, 0, 0), font=left_values_font)

        label_editable.text((10, offset + 90), l.get("date", ""), (0, 0, 0), font=brand_font2)

        text_image = Image.new('RGBA', (100, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(text_image)
        draw.text((0, 0), unit, (0, 0, 0), font=left_values_font)
        rotated_text_image = text_image.rotate(-90, expand=1, fillcolor=(255, 255, 255, 0))
        label.paste(rotated_text_image, (230, offset + 80), rotated_text_image)

        offset += 280

    label = label.rotate(90)

    buffered = BytesIO()
    label.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    buffered.seek(0)

    with open(preview_location, 'wb') as f:
        f.write(buffered.getvalue())

    return img_str


def draw_square_label(label_data, custom_field1):

    if len(label_data) == 0:
        label_data = [{"serial": "000001", "uuid": "D20240219-S000001", "cap": 3245,
                       "ip": "192.168.1.104", "slot": 1, "date": "2024-02-23"}]

    templates_folder = os.path.join(main_settings.BASE_DIR, 'static', 'labeltemplates')
    dymo_label_location = os.path.join(templates_folder, 'dymo_blank_13x25.jpg')
    preview_location = os.path.join(templates_folder, 'preview_square.jpg')
    header_font_location = os.path.join(templates_folder, 'fonts', 'OpenSans-Bold.ttf')
    left_values_font_loc = os.path.join(templates_folder, 'fonts', 'OpenSans-Regular.ttf')

    label = Image.open(dymo_label_location)
    header_font = ImageFont.truetype(header_font_location, 65)
    left_values_font = ImageFont.truetype(left_values_font_loc, 50)
    brand_font = ImageFont.truetype(left_values_font_loc, 42)
    brand_font2 = ImageFont.truetype(left_values_font_loc, 32)

    label_editable = ImageDraw.Draw(label)

    offset = 0
    l = label_data[0]

    capacity, unit = format_cap(l["cap"])

    # QR Code Block ---------
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5)

    qr.add_data("%s-C%s-%s" % (l["uuid"], capacity, unit))
    qr.make(fit=True)
    qr_img = qr.make_image(fill='black', back_color='white')
    qr_img = qr_img.crop((0, 0, 350, 350))
    qr_img = qr_img.resize((250, 250))

    label.paste(qr_img, (-30, 200))
    # QR Code Block End ---------

    serial = str(l["serial"])
    header_text = "%s-C:%s" % (serial, capacity)
    label_editable.text((20, -20), header_text, (0, 0, 0), font=header_font)

    last_ip_num = l["ip"].split(".")[-1]
    third_row = "Mc: %s-%s" % (last_ip_num, l["slot"])
    label_editable.text((5, 65), third_row, (0, 0, 0), font=left_values_font)

    # Date
    text_image2 = Image.new('RGBA', (350, 90), (255, 255, 255, 0))
    draw2 = ImageDraw.Draw(text_image2)
    draw2.text((0, 0), l["date"], (0, 0, 0), font=left_values_font)
    rotated_text_image = text_image2.rotate(-90, expand=1, fillcolor=(255, 255, 255, 0))
    label.paste(rotated_text_image, (290, 120), rotated_text_image)

    # Adding the unit
    text_image = Image.new('RGBA', (120, 100), (255, 255, 255, 0))  # Adjust size as needed
    draw = ImageDraw.Draw(text_image)

    draw.text((0, 0), unit, (0, 0, 0), font=brand_font)

    label.paste(text_image, (370, 50), text_image)


    buffered = BytesIO()
    label.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    buffered.seek(0)

    with open(preview_location, 'wb') as f:
        f.write(buffered.getvalue())

    return img_str


def draw_landscape_label(label_data, custom_field1):

    if len(label_data) == 0:
        label_data = [
            {"serial": "000001", "uuid": "D20240223-S000001", "cap": 3245,
             "ip": "192.168.1.104", "slot": 1, "date": "2024-02-23"}]

    templates_folder = os.path.join(main_settings.BASE_DIR, 'static', 'labeltemplates')
    dymo_label_location = os.path.join(templates_folder, 'phomemo_blank_30x20.jpg')
    preview_location = os.path.join(templates_folder, 'preview_lndscp.jpg')
    header_font_location = os.path.join(templates_folder, 'fonts', 'OpenSans-Bold.ttf')
    left_values_font_loc = os.path.join(templates_folder, 'fonts', 'OpenSans-Regular.ttf')

    label = Image.open(dymo_label_location)
    header_font = ImageFont.truetype(header_font_location, 62)
    left_values_font = ImageFont.truetype(left_values_font_loc, 46)
    brand_font = ImageFont.truetype(left_values_font_loc, 42)
    brand_font2 = ImageFont.truetype(left_values_font_loc, 32)

    label_editable = ImageDraw.Draw(label)

    offset = 0
    l = label_data[0]

    capacity, unit = format_cap(l["cap"])

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data("%s-C%s-%s" % (l["uuid"], capacity, unit))
    qr.make(fit=True)
    qr_img = qr.make_image(fill='black', back_color='white')
    qr_img = qr_img.crop((0, 0, 350, 350))
    qr_img = qr_img.resize((190, 190))
    label.paste(qr_img, (260, 80))

    serial = str(l["serial"])
    header_text = "%s-C:%s" % (serial, capacity)
    label_editable.text((5, -20), header_text, (0, 0, 0), font=header_font)

    last_ip_num = l["ip"].split(".")[-1]
    third_row = "Mc: %s-%s" % (last_ip_num, l["slot"])
    label_editable.text((5, 42), third_row, (0, 0, 0), font=left_values_font)

    label_editable.text((5, 95), l["date"], (0, 0, 0), font=brand_font2)

    text_image = Image.new('RGBA', (120, 100), (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_image)
    draw.text((0, 0), unit, (0, 0, 0), font=brand_font)
    label.paste(text_image, (330, 45), text_image)

    buffered = BytesIO()
    label.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    buffered.seek(0)

    with open(preview_location, 'wb') as f:
        f.write(buffered.getvalue())

    return img_str


def gather_label_data(deviceId, slots):
    device = get_object_or_404(Device, id=deviceId)

    filtered_slots = device.slots.filter(slot_number__in=slots).order_by('slot_number')

    label_data = []

    for slot in filtered_slots:
        acell = slot.active_cell
        match = re.search(r'-S(\d+)', acell.UUID)

        if match:
            # Keep the full serial number string (e.g. "005450")
            cserial = match.group(1)
        else:
            cserial = "000000"

        formated_date = acell.insertion_date.strftime('%Y-%m-%d')

        ldat = {"serial": cserial, "uuid": acell.UUID, "cap": acell.capacity, "esr": acell.esr,
                "temp": acell.max_temp_discharging, "minV": acell.min_voltage,
                "storeV": acell.store_voltage, "maxV": acell.max_voltage,
                "ip": device.ip, "slot": slot.slot_number, "date": formated_date}

        label_data.append(ldat)

    return label_data


def gather_label_cell_data(cells):

    filtered_cells = Cells.objects.filter(id__in=cells).order_by('id')

    label_data = []

    for acell in filtered_cells:
        match = re.search(r'-S(\d+)', acell.UUID)

        if match:
            # Keep the full serial number string (e.g. "005450")
            cserial = match.group(1)
        else:
            cserial = "000000"

        formated_date = acell.insertion_date.strftime('%Y-%m-%d')

        ldat = {"serial": cserial, "uuid": acell.UUID, "cap": acell.capacity, "esr": acell.esr,
                "temp": acell.max_temp_discharging, "minV": acell.min_voltage,
                "storeV": acell.store_voltage, "maxV": acell.max_voltage,
                "ip": acell.device_ip, "slot": acell.device_slot, "date": formated_date}

        label_data.append(ldat)

    return label_data


def generate_battery_uuid():
    # Query the last cell for the given project ID, ordered by ID to get the most recent one
    last_battery = Batteries.objects.order_by('-id').first()

    if last_battery:
        # Extract the serial number from the last cell's UUID
        match = re.search(r'-S(\d+)', last_battery.UUID)
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

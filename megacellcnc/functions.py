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
from .label_layout import (
    merge_battery_layout,
    merge_cell_layout,
    PREVIEW_BATTERY_LABEL_DICT,
)
from .label_layout_absolute import merge_absolute_defaults, FONT_REF
from io import BytesIO
import ipaddress


def _find_templates_folder():
    """Resolve the labeltemplates folder in both dev and PyInstaller dist."""
    candidates = [
        os.path.join(main_settings.BASE_DIR, 'static', 'labeltemplates'),
    ]
    internal = os.path.join(str(main_settings.BASE_DIR), '_internal')
    if os.path.isdir(internal):
        for name in ('megacnc_dt_static', 'static'):
            candidates.append(os.path.join(internal, name, 'labeltemplates'))
    for name in ('megacnc_dt_static', 'static'):
        candidates.append(os.path.join(str(main_settings.BASE_DIR), name, 'labeltemplates'))
    for c in candidates:
        if os.path.isdir(c):
            return c
    return candidates[0]


_templates_folder_cache = None

def _get_templates_folder():
    global _templates_folder_cache
    if _templates_folder_cache is None:
        _templates_folder_cache = _find_templates_folder()
    return _templates_folder_cache

def extract_segment(host):
    # Define a regex pattern to capture the segment between the first hyphen and the first dot
    pattern = r'-([^.]+)\.'

    # Search for the pattern in the provided hostname
    match = re.search(pattern, host)

    # If a match is found, return the captured group, otherwise return None or an appropriate default value
    return match.group(1) if match else None


def portscan(port, host, res_dict):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)  # Timeout for the socket operation
    result = sock.connect_ex((host, port))
    if result == 0:
        res_dict[host] = result
    sock.close()


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

        last_three_parts = mac_address.split(":")[-3:]
        device_name = tester_type + "-" + "".join(last_three_parts)

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

                last_three_parts = mac_address.split(":")[-3:]
                device_name = tester_type + "-" + "".join(last_three_parts)

                devices_list.append({'id': dev_id, 'name': device_name, 'ip': manual_ip, 'type': tester_type, 'mac': mac_address, 'slot_count': slot_count,
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
    project_instance.update_total_cells()
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

    templates_folder = _get_templates_folder()
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

        # QR Code Block ---
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=5)

        qr.add_data("%s-C%s-%s" % (l["uuid"], capacity, unit))
        qr.make(fit=True)
        qr_img = qr.make_image(fill='black', back_color='white')
        qr_img = qr_img.crop((0, 0, 350, 350))
        qr_img = qr_img.resize((220, 220))

        label.paste(qr_img, (300, offset + 30))
        # QR Code Bloc End ---

        serial = str(l["serial"]).zfill(6)
        header_text = "%s-C:%s" % (serial, capacity)
        label_editable.text((10, offset + -20), header_text, (0, 0, 0), font=header_font)

        first_row = "I:%s T:%s" % (l["esr"], l["temp"])
        label_editable.text((10, offset + 40), first_row, (0, 0, 0), font=left_values_font)

        second_row = "%s/%s/%s" % (l["minV"], l["storeV"], l["maxV"])
        label_editable.text((10, offset + 80), second_row, (0, 0, 0), font=left_values_font)

        last_ip_num = l["ip"].split(".")[-1]
        third_row = "Mc: %s-%s" % (last_ip_num, l["slot"])
        label_editable.text((10, offset + 130), third_row, (0, 0, 0), font=left_values_font)

        # Adding the unit
        text_image = Image.new('RGBA', (100, 100), (255, 255, 255, 0))  # Adjust size as needed
        draw = ImageDraw.Draw(text_image)

        draw.text((0, 0), unit, (0, 0, 0), font=left_values_font)
        rotated_text_image = text_image.rotate(-90, expand=1, fillcolor=(255, 255, 255, 0))

        label.paste(rotated_text_image, (230, offset + 80), rotated_text_image)

        deep_row = "deepcyclepower.com"
        label_editable.text((5, offset + 180), deep_row, (0, 0, 0), font=brand_font2)


        offset += 280

    label = label.rotate(90)

    buffered = BytesIO()
    label.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    buffered.seek(0)

    with open(preview_location, 'wb') as f:
        f.write(buffered.getvalue())

    return img_str


def draw_square_label(label_data, custom_field1, layout=None):
    """
    Cell label (square template). Uses v2 absolute layout when available.
    """
    if isinstance(layout, dict) and layout.get('layout_mode') == 'absolute':
        L = layout
    else:
        L = {}
    if len(label_data) == 0:
        label_data = [{"serial": 1, "uuid": "D20240219-S000001", "cap": 3245, "esr": 0.1, "temp": 25, "minV": 2.8, "storeV": 3.7, "maxV": 4.24,
                       "ip": "192.168.1.104", "slot": 1, "date": "2024-02-23"}]

    templates_folder = _get_templates_folder()
    preview_location = os.path.join(templates_folder, 'preview_square.jpg')
    l = label_data[0]
    capacity, unit = format_cap(l["cap"])

    if L.get('layout_mode') == 'absolute':
        La = merge_absolute_defaults('square', L)
        return _render_square_absolute(La, l, capacity, unit, custom_field1, preview_location)

    # Legacy hard-coded square renderer (fallback)
    header_font_location = os.path.join(templates_folder, 'fonts', 'OpenSans-Bold.ttf')
    left_values_font_loc = os.path.join(templates_folder, 'fonts', 'OpenSans-Regular.ttf')

    cw, ch = 500, 480
    label = Image.new('RGB', (cw, ch), (255, 255, 255))
    header_font = ImageFont.truetype(header_font_location, 65)
    left_values_font = ImageFont.truetype(left_values_font_loc, 50)
    brand_font = ImageFont.truetype(left_values_font_loc, 42)
    brand_font2 = ImageFont.truetype(left_values_font_loc, 32)
    label_editable = ImageDraw.Draw(label)

    serial = str(l["serial"]).zfill(6)
    header_text = "%s-C:%s" % (serial, capacity)
    label_editable.text((20, 5), header_text, (0, 0, 0), font=header_font)
    first_row = "I:%s T:%s" % (l["esr"], l["temp"])
    label_editable.text((5, 75), first_row, (0, 0, 0), font=left_values_font)
    second_row = "%s/%s/%s" % (l["minV"], l["storeV"], l["maxV"])
    label_editable.text((5, 125), second_row, (0, 0, 0), font=left_values_font)
    last_ip_num = l["ip"].split(".")[-1]
    third_row = "Mc: %s-%s" % (last_ip_num, l["slot"])
    label_editable.text((5, 175), third_row, (0, 0, 0), font=left_values_font)

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data("%s-C%s-%s" % (l["uuid"], capacity, unit))
    qr.make(fit=True)
    qr_img = qr.make_image(fill='black', back_color='white')
    qr_img = qr_img.crop((0, 0, 350, 350))
    qr_img = qr_img.resize((220, 220))
    label.paste(qr_img, (10, 240))

    text_image = Image.new('RGBA', (350, 50), (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_image)
    draw.text((0, 0), LABEL_BRAND_URL, (0, 0, 0), font=brand_font2)
    rotated_text_image = text_image.rotate(-90, expand=1, fillcolor=(255, 255, 255, 0))
    label.paste(rotated_text_image, (450, 120), rotated_text_image)

    text_image2 = Image.new('RGBA', (350, 90), (255, 255, 255, 0))
    draw2 = ImageDraw.Draw(text_image2)
    draw2.text((0, 0), l["date"], (0, 0, 0), font=left_values_font)
    rotated_text_image = text_image2.rotate(-90, expand=1, fillcolor=(255, 255, 255, 0))
    label.paste(rotated_text_image, (290, 120), rotated_text_image)

    label_editable.text((20, 425), custom_field1 or '', (0, 0, 0), font=brand_font)

    text_image = Image.new('RGBA', (120, 100), (255, 255, 255, 0))
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


def _render_square_absolute(La, l, capacity, unit, custom_field1, preview_path):
    """Absolute renderer for square cell labels — same fields as landscape cell."""
    templates_folder = _get_templates_folder()
    header_font_location = os.path.join(templates_folder, 'fonts', 'OpenSans-Bold.ttf')
    left_values_font_loc = os.path.join(templates_folder, 'fonts', 'OpenSans-Regular.ttf')

    cw = max(120, int(La.get('canvas_w_px') or 500))
    ch = max(80, int(La.get('canvas_h_px') or 480))

    if La.get('use_template_bg'):
        tpl = os.path.join(templates_folder, 'dymo_blank_13x25.jpg')
        if os.path.isfile(tpl):
            bg = Image.open(tpl).convert('RGB').resize((cw, ch))
            label = bg.copy()
        else:
            label = Image.new('RGB', (cw, ch), (255, 255, 255))
    else:
        label = Image.new('RGB', (cw, ch), (255, 255, 255))

    draw = ImageDraw.Draw(label)
    elems = La.get('elements') or {}
    serial = str(l['serial']).zfill(6)
    cap_text = unit

    def font_for(el, role):
        pt = _pt_for_element_role(role, el, cw, ch)
        return ImageFont.truetype(header_font_location if role == 'header' else left_values_font_loc, pt)

    order = ['header', 'esr_temp', 'voltages', 'mc_slot', 'date', 'custom']
    for key in order:
        el = elems.get(key)
        if not el or not el.get('show', True):
            continue
        role = el.get('role') or ('header' if key == 'header' else ('small' if key in ('date', 'custom') else 'body'))
        x0 = int(float(el['x']) * cw)
        y0 = int(float(el['y']) * ch)
        tw = max(20, int(float(el['w']) * cw))
        th = max(8, int(float(el.get('h', 0.1)) * ch))
        font = font_for(el, role)
        rot = int(el.get('rotate') or 0) % 360

        if key == 'header':
            header_text = '%s-C:%s' % (serial, capacity)
            if rot != 0:
                _draw_rotated_text_in_box(label, x0, y0, tw, th, '%s    %s' % (header_text, cap_text), font, rot)
            else:
                if int(el.get('font') or 0) > 0:
                    pt = int(el['font'])
                    hf = ImageFont.truetype(header_font_location, pt)
                    bf = ImageFont.truetype(left_values_font_loc, pt)
                else:
                    hf = ImageFont.truetype(header_font_location, _pt_for_element_role('header', el, cw, ch))
                    bf = ImageFont.truetype(left_values_font_loc, _pt_for_element_role('body', el, cw, ch))
                cap_w = _label_text_width(draw, cap_text, bf)
                hdr_w = _label_text_width(draw, header_text, hf)
                lh_h = _label_line_height(draw, hf) + 2
                lh_b = _label_line_height(draw, bf) + 2
                yb = y0 + th
                if hdr_w + cap_w + 10 <= tw and y0 + max(lh_h, lh_b) <= yb:
                    draw.text((x0, y0), header_text, (0, 0, 0), font=hf)
                    draw.text((x0 + tw - cap_w, y0), cap_text, (0, 0, 0), font=bf)
                else:
                    yy = y0
                    for line in _label_wrap_lines(draw, header_text, hf, tw):
                        lhx = _label_line_height(draw, hf) + 2
                        if yy + lhx > yb:
                            break
                        draw.text((x0, yy), line, (0, 0, 0), font=hf)
                        yy += lhx
                    if yy + lh_b <= yb:
                        draw.text((x0, yy), cap_text, (0, 0, 0), font=bf)
        elif key == 'esr_temp':
            txt = 'I:%s T:%s' % (l['esr'], l['temp'])
            _draw_rotated_text_in_box(label, x0, y0, tw, th, txt, font, rot)
        elif key == 'voltages':
            txt = '%s/%s/%s' % (l['minV'], l['storeV'], l['maxV'])
            _draw_rotated_text_in_box(label, x0, y0, tw, th, txt, font, rot)
        elif key == 'mc_slot':
            last_ip_num = l['ip'].split('.')[-1]
            txt = 'Mc: %s-%s' % (last_ip_num, l['slot'])
            _draw_rotated_text_in_box(label, x0, y0, tw, th, txt, font, rot)
        elif key == 'date':
            _draw_rotated_text_in_box(label, x0, y0, tw, th, l['date'], font, rot)
        elif key == 'custom':
            if not custom_field1:
                continue
            _draw_rotated_text_in_box(label, x0, y0, tw, th, custom_field1, font, rot)

    qel = elems.get('qr')
    if qel and qel.get('show', True):
        qs = float(qel.get('size', 0.42))
        qr_size = int(qs * min(cw, ch))
        qx = int(float(qel['x']) * cw)
        qy = int(float(qel['y']) * ch)
        qr_size = max(40, min(qr_size, cw - qx, ch - qy))
        box = max(4, min(14, int(qr_size / 22)))
        border = int(La.get('qr_border', 3))
        qr_obj = qrcode.QRCode(version=1, box_size=box, border=border)
        qr_obj.add_data('%s-C%s-%s' % (l['uuid'], capacity, unit))
        qr_obj.make(fit=True)
        qr_img = qr_obj.make_image(fill='black', back_color='white')
        qiw, qih = qr_img.size
        crop = min(qiw, qih, 400)
        qr_img = qr_img.crop((0, 0, crop, crop))
        qr_img = qr_img.resize((qr_size, qr_size))
        label.paste(qr_img, (qx, qy))

    draw = ImageDraw.Draw(label)
    _draw_brand_url_fixed_bottom(draw, elems, cw, ch, left_values_font_loc)

    buffered = BytesIO()
    label.save(buffered, format='JPEG')
    img_str = base64.b64encode(buffered.getvalue()).decode()
    buffered.seek(0)
    with open(preview_path, 'wb') as f:
        f.write(buffered.getvalue())
    return img_str


def draw_landscape_label(label_data, custom_field1, layout=None):
    """
    Cell label (landscape template). QR bottom-right; layout from PrinterSettings JSON.
    """
    if isinstance(layout, dict) and layout.get('layout_mode') == 'absolute':
        L = layout
    else:
        L = merge_cell_layout(layout)
    if len(label_data) == 0:
        label_data = [
            {"serial": 1, "uuid": "D20240223-S000001", "cap": 3245, "esr": 0.1, "temp": 25, "minV": 2.8, "storeV": 3.7,
             "maxV": 4.24,
             "ip": "192.168.1.104", "slot": 1, "date": "2024-02-23"}]

    templates_folder = _get_templates_folder()
    preview_location = os.path.join(templates_folder, 'preview_lndscp.jpg')
    l = label_data[0]
    capacity, unit = format_cap(l["cap"])
    if L.get('layout_mode') == 'absolute':
        La = merge_absolute_defaults('cell', L)
        return _render_cell_absolute(La, l, capacity, unit, custom_field1, preview_location)

    dymo_label_location = os.path.join(templates_folder, 'phomemo_blank_30x20.jpg')
    header_font_location = os.path.join(templates_folder, 'fonts', 'OpenSans-Bold.ttf')
    left_values_font_loc = os.path.join(templates_folder, 'fonts', 'OpenSans-Regular.ttf')

    label = Image.open(dymo_label_location)
    w, h = label.size

    h_pt = int(L.get('font_header_pt') or 0)
    b_pt = int(L.get('font_body_pt') or 0)
    s_pt = int(L.get('font_small_pt') or 0)
    if h_pt <= 0:
        h_pt = 48 if w < 430 else 52
    if b_pt <= 0:
        b_pt = 34 if w < 430 else 38
    if s_pt <= 0:
        s_pt = 28 if w < 430 else 30

    header_font = ImageFont.truetype(header_font_location, h_pt)
    left_values_font = ImageFont.truetype(left_values_font_loc, b_pt)
    brand_font2 = ImageFont.truetype(left_values_font_loc, s_pt)

    label_editable = ImageDraw.Draw(label)

    margin = int(L.get('margin_px', 10))
    min_text_column = int(L.get('min_text_column_px', 130))
    text_qr_gap = int(L.get('text_qr_gap_px', 14))
    qf = float(L.get('qr_frac', 0.52))
    qmin = int(L.get('qr_min_px', 150))
    qmax = int(L.get('qr_max_px', 210))

    max_qr = min(w - margin * 2 - min_text_column, h - margin * 2 - 8)
    qr_size = int(min(w, h) * qf)
    qr_size = max(qmin, min(qmax, qr_size))
    qr_size = min(qr_size, max_qr)
    qr_x = w - qr_size - margin
    qr_y = h - qr_size - margin
    text_max_w = max(120, qr_x - margin - text_qr_gap)

    x0 = margin
    y = margin

    serial = str(l["serial"]).zfill(6)
    cap_text = unit
    lh_body = _label_line_height(label_editable, left_values_font) + 2

    if L.get('show_header', True):
        header_text = "%s-C:%s" % (serial, capacity)
        cap_w = _label_text_width(label_editable, cap_text, left_values_font)
        hdr_w = _label_text_width(label_editable, header_text, header_font)
        if hdr_w + cap_w + 12 <= text_max_w:
            label_editable.text((x0, y), header_text, (0, 0, 0), font=header_font)
            label_editable.text((x0 + text_max_w - cap_w, y), cap_text, (0, 0, 0), font=left_values_font)
        else:
            label_editable.text((x0, y), header_text, (0, 0, 0), font=header_font)
            y += _label_line_height(label_editable, header_font) + 2
            label_editable.text((x0, y), cap_text, (0, 0, 0), font=left_values_font)
        y += _label_line_height(label_editable, header_font) + 6
    else:
        label_editable.text((x0, y), cap_text, (0, 0, 0), font=left_values_font)
        y += lh_body

    if L.get('show_esr_temp', True):
        first_row = "I:%s T:%s" % (l["esr"], l["temp"])
        for line in _label_wrap_lines(label_editable, first_row, left_values_font, text_max_w):
            label_editable.text((x0, y), line, (0, 0, 0), font=left_values_font)
            y += lh_body

    if L.get('show_voltages', True):
        second_row = "%s/%s/%s" % (l["minV"], l["storeV"], l["maxV"])
        for line in _label_wrap_lines(label_editable, second_row, left_values_font, text_max_w):
            label_editable.text((x0, y), line, (0, 0, 0), font=left_values_font)
            y += lh_body

    if L.get('show_mc_slot', True):
        last_ip_num = l["ip"].split(".")[-1]
        third_row = "Mc: %s-%s" % (last_ip_num, l["slot"])
        for line in _label_wrap_lines(label_editable, third_row, left_values_font, text_max_w):
            label_editable.text((x0, y), line, (0, 0, 0), font=left_values_font)
            y += lh_body

    y += 2
    lh_small = _label_line_height(label_editable, brand_font2) + 3
    if L.get('show_date', True):
        label_editable.text((x0, y), l["date"], (0, 0, 0), font=brand_font2)
        y += lh_small
    if L.get('show_custom_footer', True) and custom_field1:
        label_editable.text((x0, y), custom_field1, (0, 0, 0), font=brand_font2)
        y += lh_small
    if L.get('show_brand_url', True):
        label_editable.text((x0, y), 'deepcyclepower.com', (0, 0, 0), font=brand_font2)

    qr = qrcode.QRCode(
        version=1,
        box_size=int(L.get('qr_box_size', 9)),
        border=int(L.get('qr_border', 3)))
    qr.add_data("%s-C%s-%s" % (l["uuid"], capacity, unit))
    qr.make(fit=True)
    qr_img = qr.make_image(fill='black', back_color='white')
    qiw, qih = qr_img.size
    crop = min(qiw, qih, 400)
    qr_img = qr_img.crop((0, 0, crop, crop))
    qr_img = qr_img.resize((qr_size, qr_size))
    label.paste(qr_img, (qr_x, qr_y))

    buffered = BytesIO()
    label.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    buffered.seek(0)

    with open(preview_location, 'wb') as f:
        f.write(buffered.getvalue())

    return img_str


def gather_battery_label_dict(battery):
    """
    Build display dict for pack label / QR. Capacity uses stored value or sum of assigned cells.
    """
    cap = float(battery.capacity or 0)
    if cap <= 0:
        try:
            cells = battery.battery_cells.all()
            if cells:
                cap = sum(float(c.capacity or 0) for c in cells)
        except Exception:
            pass
    match = re.search(r'-S(\d+)', battery.UUID)
    serial = int(match.group(1)) if match else 0
    mfg = battery.manufacturing_date
    if mfg is None:
        mfg = battery.creation_date.date() if battery.creation_date else timezone.now().date()
    date_str = mfg.strftime('%Y-%m-%d') if hasattr(mfg, 'strftime') else str(mfg)
    s = battery.series or 0
    p = battery.parallel or 0
    config = f"{s}S{p}P" if s and p else ''
    return {
        'serial': serial,
        'serial_str': str(serial).zfill(6),
        'uuid': battery.UUID,
        'cap': cap,
        'name': battery.name or '',
        'esr': battery.pack_esr,
        'notes': (battery.notes or '')[:120],
        'date': date_str,
        'configuration': config,
    }


def _label_text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _label_line_height(draw, font, sample='Hg'):
    bbox = draw.textbbox((0, 0), sample, font=font)
    return bbox[3] - bbox[1]


def _label_wrap_lines(draw, text, font, max_width):
    """Split text into lines that fit within max_width (pixels). Handles long UUIDs."""
    if not text:
        return []
    words = text.split()
    lines = []
    cur = []
    for word in words:
        test = ' '.join(cur + [word]) if cur else word
        if _label_text_width(draw, test, font) <= max_width:
            cur.append(word)
            continue
        if cur:
            lines.append(' '.join(cur))
            cur = []
        if _label_text_width(draw, word, font) <= max_width:
            cur.append(word)
            continue
        chunk = ''
        for ch in word:
            t = chunk + ch
            if _label_text_width(draw, t, font) <= max_width:
                chunk = t
            else:
                if chunk:
                    lines.append(chunk)
                chunk = ch
        if chunk:
            cur.append(chunk)
    if cur:
        lines.append(' '.join(cur))
    return lines


# Fixed brand URL on absolute layouts (cannot be removed via layout JSON)
LABEL_BRAND_URL = 'deepcyclepower.com'


def _brand_font_pt(el, _cw, _ch):
    """Brand line always uses LABEL_BRAND_URL; min 12 pt, 0/auto maps to 12."""
    ov = int(el.get('font') or 0)
    if ov <= 0:
        return 12
    return max(12, min(80, ov))


def _pt_for_element_role(role, el, cw, ch):
    ref = min(cw, ch)
    ov = int(el.get('font') or 0)
    if ov > 0:
        return max(8, ov)
    if role == 'header':
        base = 52
    elif role == 'small':
        base = 30
    else:
        base = 38
    return max(10, int(base * ref / FONT_REF))


def _draw_wrapped_text_in_box(draw, x0, y0, tw, th, text, font, fill=(0, 0, 0)):
    """Draw text wrapped to width tw; stop when exceeding box height th."""
    if not text or th <= 0 or tw <= 0:
        return
    yb = y0 + th
    yy = y0
    for line in _label_wrap_lines(draw, text, font, tw):
        lh = _label_line_height(draw, font) + 2
        if yy + lh > yb:
            break
        draw.text((x0, yy), line, fill, font=font)
        yy += lh


def _draw_rotated_text_in_box(label, x0, y0, tw, th, text, font, rotate_deg, fill=(0, 0, 0)):
    """Draw wrapped text inside a box, optionally rotated by 90/180/270 degrees.

    For 0 degrees, draws directly onto `label` (fast path).
    For other angles, renders text at original box size, rotates, and centers
    the result on the box midpoint — matching CSS transform-origin: center.
    """
    rotate_deg = int(rotate_deg or 0) % 360
    if rotate_deg == 0:
        draw = ImageDraw.Draw(label)
        _draw_wrapped_text_in_box(draw, x0, y0, tw, th, text, font, fill)
        return

    tmp = Image.new('RGBA', (tw, th), (255, 255, 255, 0))
    tmp_draw = ImageDraw.Draw(tmp)
    _draw_wrapped_text_in_box(tmp_draw, 0, 0, tw, th, text, font, fill)

    rotated = tmp.rotate(-rotate_deg, expand=True, fillcolor=(255, 255, 255, 0))
    rw, rh = rotated.size
    cx = x0 + tw // 2
    cy = y0 + th // 2
    label.paste(rotated, (cx - rw // 2, cy - rh // 2), rotated)


def _draw_brand_url_fixed_bottom(draw, elems, cw, ch, left_values_font_loc):
    """
    Always draw deepcyclepower.com as a watermark strip pinned to the very
    bottom of the label.  A white background ensures readability even when
    overlapping the QR code.  Font scales with canvas height so it stays
    visible in scaled-down previews.
    """
    if not isinstance(elems, dict):
        return
    el = elems.get('brand')
    if not isinstance(el, dict):
        return
    min_auto = max(12, int(ch * 0.035))
    user_pt = int(el.get('font') or 0)
    pt = max(min_auto, user_pt) if user_pt > 0 else min_auto
    pt = min(pt, 80)
    font = ImageFont.truetype(left_values_font_loc, pt)
    pad_x = max(4, int(0.02 * cw))
    lh = _label_line_height(draw, font) + 2
    th = lh + 6
    y0 = ch - th
    tw = max(40, cw - 2 * pad_x)
    draw.rectangle([0, y0, cw, ch], fill=(255, 255, 255))
    _draw_wrapped_text_in_box(draw, pad_x, y0 + 2, tw, th - 2, LABEL_BRAND_URL, font)


def _render_battery_absolute(La, l, capacity, unit, custom_field1, preview_path):
    templates_folder = _get_templates_folder()
    header_font_location = os.path.join(templates_folder, 'fonts', 'OpenSans-Bold.ttf')
    left_values_font_loc = os.path.join(templates_folder, 'fonts', 'OpenSans-Regular.ttf')

    cw = int(La.get('canvas_w_px') or 520)
    ch = int(La.get('canvas_h_px') or 360)
    cw = max(120, cw)
    ch = max(80, ch)

    if La.get('use_template_bg'):
        tpl = os.path.join(templates_folder, 'phomemo_blank_30x20.jpg')
        if os.path.isfile(tpl):
            bg = Image.open(tpl).convert('RGB').resize((cw, ch))
            label = bg.copy()
        else:
            label = Image.new('RGB', (cw, ch), (255, 255, 255))
    else:
        label = Image.new('RGB', (cw, ch), (255, 255, 255))

    draw = ImageDraw.Draw(label)
    elems = La.get('elements') or {}
    serial = l.get('serial_str') or str(l.get('serial', 0)).zfill(6)

    def font_for(el, role):
        pt = _pt_for_element_role(role, el, cw, ch)
        return ImageFont.truetype(header_font_location if role == 'header' else left_values_font_loc, pt)

    order = ['header', 'name_cap', 'config', 'esr', 'notes', 'mfg', 'custom']
    for key in order:
        el = elems.get(key)
        if not el or not el.get('show', True):
            continue
        role = el.get('role') or ('header' if key == 'header' else ('small' if key in ('notes', 'mfg', 'custom', 'brand') else 'body'))
        x0 = int(float(el['x']) * cw)
        y0 = int(float(el['y']) * ch)
        tw = max(20, int(float(el['w']) * cw))
        th = max(8, int(float(el.get('h', 0.1)) * ch))
        font = font_for(el, role)
        rot = int(el.get('rotate') or 0) % 360

        if key == 'header':
            txt = 'PACK %s-C:%s' % (serial, capacity)
            _draw_rotated_text_in_box(label, x0, y0, tw, th, txt, font, rot)
        elif key == 'name_cap':
            name = (l.get('name') or 'Battery pack')[:80]
            cap_text = '%s %s' % (capacity, unit)
            if rot != 0:
                _draw_rotated_text_in_box(label, x0, y0, tw, th, '%s  %s' % (name, cap_text), font, rot)
            else:
                cap_w = _label_text_width(draw, cap_text, font)
                name_w = _label_text_width(draw, name, font)
                lh = _label_line_height(draw, font) + 2
                yb = y0 + th
                if name_w + cap_w + 10 <= tw and y0 + lh <= yb:
                    draw.text((x0, y0), name, (0, 0, 0), font=font)
                    draw.text((x0 + tw - cap_w, y0), cap_text, (0, 0, 0), font=font)
                else:
                    yy = y0
                    for line in _label_wrap_lines(draw, name, font, tw):
                        if yy + lh > yb:
                            break
                        draw.text((x0, yy), line, (0, 0, 0), font=font)
                        yy += lh
                    if yy + lh <= yb:
                        draw.text((x0, yy), cap_text, (0, 0, 0), font=font)
        elif key == 'config':
            row = '%s  %s' % (l.get('configuration') or '', serial) if l.get('configuration') else serial
            _draw_rotated_text_in_box(label, x0, y0, tw, th, row.strip(), font, rot)
        elif key == 'esr':
            esr_txt = ('ESR: %s' % l.get('esr')) if l.get('esr') is not None else 'ESR: —'
            _draw_rotated_text_in_box(label, x0, y0, tw, th, esr_txt, font, rot)
        elif key == 'notes':
            notes = (l.get('notes') or '')[:120]
            if not notes:
                continue
            _draw_rotated_text_in_box(label, x0, y0, tw, th, notes, font, rot)
        elif key == 'mfg':
            _draw_rotated_text_in_box(label, x0, y0, tw, th, 'Mfg: %s' % l.get('date', ''), font, rot)
        elif key == 'custom':
            if not custom_field1:
                continue
            _draw_rotated_text_in_box(label, x0, y0, tw, th, custom_field1, font, rot)

    qel = elems.get('qr')
    if qel and qel.get('show', True):
        qs = float(qel.get('size', 0.35))
        qr_size = int(qs * min(cw, ch))
        qx = int(float(qel['x']) * cw)
        qy = int(float(qel['y']) * ch)
        qr_size = max(40, min(qr_size, cw - qx, ch - qy))
        box = max(4, min(14, int(qr_size / 22)))
        border = int(La.get('qr_border', 3))
        qr = qrcode.QRCode(version=1, box_size=box, border=border)
        qr.add_data('%s-C%s-%s' % (l['uuid'], capacity, unit))
        qr.make(fit=True)
        qr_img = qr.make_image(fill='black', back_color='white')
        qiw, qih = qr_img.size
        crop = min(qiw, qih, 400)
        qr_img = qr_img.crop((0, 0, crop, crop))
        qr_img = qr_img.resize((qr_size, qr_size))
        label.paste(qr_img, (qx, qy))

    draw = ImageDraw.Draw(label)
    _draw_brand_url_fixed_bottom(draw, elems, cw, ch, left_values_font_loc)

    buffered = BytesIO()
    label.save(buffered, format='JPEG')
    img_str = base64.b64encode(buffered.getvalue()).decode()
    buffered.seek(0)
    with open(preview_path, 'wb') as f:
        f.write(buffered.getvalue())
    return img_str


def _render_cell_absolute(La, l, capacity, unit, custom_field1, preview_path):
    templates_folder = _get_templates_folder()
    header_font_location = os.path.join(templates_folder, 'fonts', 'OpenSans-Bold.ttf')
    left_values_font_loc = os.path.join(templates_folder, 'fonts', 'OpenSans-Regular.ttf')

    cw = int(La.get('canvas_w_px') or 400)
    ch = int(La.get('canvas_h_px') or 280)
    cw = max(120, cw)
    ch = max(80, ch)

    if La.get('use_template_bg'):
        tpl = os.path.join(templates_folder, 'phomemo_blank_30x20.jpg')
        if os.path.isfile(tpl):
            bg = Image.open(tpl).convert('RGB').resize((cw, ch))
            label = bg.copy()
        else:
            label = Image.new('RGB', (cw, ch), (255, 255, 255))
    else:
        label = Image.new('RGB', (cw, ch), (255, 255, 255))

    draw = ImageDraw.Draw(label)
    elems = La.get('elements') or {}
    serial = str(l['serial']).zfill(6)
    cap_text = unit

    def font_for(el, role):
        pt = _pt_for_element_role(role, el, cw, ch)
        return ImageFont.truetype(header_font_location if role == 'header' else left_values_font_loc, pt)

    order = ['header', 'esr_temp', 'voltages', 'mc_slot', 'date', 'custom']
    for key in order:
        el = elems.get(key)
        if not el or not el.get('show', True):
            continue
        role = el.get('role') or ('header' if key == 'header' else ('small' if key in ('date', 'custom', 'brand') else 'body'))
        x0 = int(float(el['x']) * cw)
        y0 = int(float(el['y']) * ch)
        tw = max(20, int(float(el['w']) * cw))
        th = max(8, int(float(el.get('h', 0.1)) * ch))
        font = font_for(el, role)
        rot = int(el.get('rotate') or 0) % 360

        if key == 'header':
            header_text = '%s-C:%s' % (serial, capacity)
            if rot != 0:
                _draw_rotated_text_in_box(label, x0, y0, tw, th, '%s    %s' % (header_text, cap_text), font, rot)
            else:
                if int(el.get('font') or 0) > 0:
                    pt = int(el['font'])
                    hf = ImageFont.truetype(header_font_location, pt)
                    bf = ImageFont.truetype(left_values_font_loc, pt)
                else:
                    hf = ImageFont.truetype(header_font_location, _pt_for_element_role('header', el, cw, ch))
                    bf = ImageFont.truetype(left_values_font_loc, _pt_for_element_role('body', el, cw, ch))
                cap_w = _label_text_width(draw, cap_text, bf)
                hdr_w = _label_text_width(draw, header_text, hf)
                lh_h = _label_line_height(draw, hf) + 2
                lh_b = _label_line_height(draw, bf) + 2
                yb = y0 + th
                if hdr_w + cap_w + 10 <= tw and y0 + max(lh_h, lh_b) <= yb:
                    draw.text((x0, y0), header_text, (0, 0, 0), font=hf)
                    draw.text((x0 + tw - cap_w, y0), cap_text, (0, 0, 0), font=bf)
                else:
                    yy = y0
                    for line in _label_wrap_lines(draw, header_text, hf, tw):
                        lhx = _label_line_height(draw, hf) + 2
                        if yy + lhx > yb:
                            break
                        draw.text((x0, yy), line, (0, 0, 0), font=hf)
                        yy += lhx
                    if yy + lh_b <= yb:
                        draw.text((x0, yy), cap_text, (0, 0, 0), font=bf)
        elif key == 'esr_temp':
            txt = 'I:%s T:%s' % (l['esr'], l['temp'])
            _draw_rotated_text_in_box(label, x0, y0, tw, th, txt, font, rot)
        elif key == 'voltages':
            txt = '%s/%s/%s' % (l['minV'], l['storeV'], l['maxV'])
            _draw_rotated_text_in_box(label, x0, y0, tw, th, txt, font, rot)
        elif key == 'mc_slot':
            last_ip_num = l['ip'].split('.')[-1]
            txt = 'Mc: %s-%s' % (last_ip_num, l['slot'])
            _draw_rotated_text_in_box(label, x0, y0, tw, th, txt, font, rot)
        elif key == 'date':
            _draw_rotated_text_in_box(label, x0, y0, tw, th, l['date'], font, rot)
        elif key == 'custom':
            if not custom_field1:
                continue
            _draw_rotated_text_in_box(label, x0, y0, tw, th, custom_field1, font, rot)

    qel = elems.get('qr')
    if qel and qel.get('show', True):
        qs = float(qel.get('size', 0.35))
        qr_size = int(qs * min(cw, ch))
        qx = int(float(qel['x']) * cw)
        qy = int(float(qel['y']) * ch)
        qr_size = max(40, min(qr_size, cw - qx, ch - qy))
        box = max(4, min(14, int(qr_size / 22)))
        border = int(La.get('qr_border', 3))
        qr = qrcode.QRCode(version=1, box_size=box, border=border)
        qr.add_data('%s-C%s-%s' % (l['uuid'], capacity, unit))
        qr.make(fit=True)
        qr_img = qr.make_image(fill='black', back_color='white')
        qiw, qih = qr_img.size
        crop = min(qiw, qih, 400)
        qr_img = qr_img.crop((0, 0, crop, crop))
        qr_img = qr_img.resize((qr_size, qr_size))
        label.paste(qr_img, (qx, qy))

    draw = ImageDraw.Draw(label)
    _draw_brand_url_fixed_bottom(draw, elems, cw, ch, left_values_font_loc)

    buffered = BytesIO()
    label.save(buffered, format='JPEG')
    img_str = base64.b64encode(buffered.getvalue()).decode()
    buffered.seek(0)
    with open(preview_path, 'wb') as f:
        f.write(buffered.getvalue())
    return img_str


def draw_battery_pack_label(battery, custom_field1, layout=None):
    """
    Landscape-style label with QR encoding UUID-C{cap}-mAh (same pattern as cell labels).
    Text stays in a left column; QR is bottom-right so it never overlaps text.
    `battery` may be a Batteries instance or a dict (preview). `layout` from PrinterSettings JSON.
    """
    if isinstance(layout, dict) and layout.get('layout_mode') == 'absolute':
        L = layout
    else:
        L = merge_battery_layout(layout)
    if isinstance(battery, dict):
        l = battery
    else:
        l = gather_battery_label_dict(battery)
    capacity, unit = format_cap(l['cap'])

    templates_folder = _get_templates_folder()
    preview_location = os.path.join(templates_folder, 'preview_battery_pack.jpg')
    if L.get('layout_mode') == 'absolute':
        La = merge_absolute_defaults('battery', L)
        return _render_battery_absolute(La, l, capacity, unit, custom_field1, preview_location)

    dymo_label_location = os.path.join(templates_folder, 'phomemo_blank_30x20.jpg')
    header_font_location = os.path.join(templates_folder, 'fonts', 'OpenSans-Bold.ttf')
    left_values_font_loc = os.path.join(templates_folder, 'fonts', 'OpenSans-Regular.ttf')

    label = Image.open(dymo_label_location)
    w, h = label.size

    h_pt = int(L.get('font_header_pt') or 0)
    b_pt = int(L.get('font_body_pt') or 0)
    s_pt = int(L.get('font_small_pt') or 0)
    if h_pt <= 0:
        h_pt = 48 if w < 430 else 52
    if b_pt <= 0:
        b_pt = 34 if w < 430 else 38
    if s_pt <= 0:
        s_pt = 28 if w < 430 else 30

    header_font = ImageFont.truetype(header_font_location, h_pt)
    left_values_font = ImageFont.truetype(left_values_font_loc, b_pt)
    brand_font2 = ImageFont.truetype(left_values_font_loc, s_pt)

    label_editable = ImageDraw.Draw(label)

    margin = int(L.get('margin_px', 10))
    min_text_column = int(L.get('min_text_column_px', 130))
    text_qr_gap = int(L.get('text_qr_gap_px', 14))
    qf = float(L.get('qr_frac', 0.52))
    qmin = int(L.get('qr_min_px', 150))
    qmax = int(L.get('qr_max_px', 210))

    max_qr = min(w - margin * 2 - min_text_column, h - margin * 2 - 8)
    qr_size = int(min(w, h) * qf)
    qr_size = max(qmin, min(qmax, qr_size))
    qr_size = min(qr_size, max_qr)
    qr_x = w - qr_size - margin
    qr_y = h - qr_size - margin
    text_max_w = max(120, qr_x - margin - text_qr_gap)

    x0 = margin
    y = margin

    serial = l.get('serial_str') or str(l['serial']).zfill(6)
    lh_body = _label_line_height(label_editable, left_values_font) + 2

    if L.get('show_header', True):
        header_text = 'PACK %s-C:%s' % (serial, capacity)
        label_editable.text((x0, y), header_text, (0, 0, 0), font=header_font)
        y += _label_line_height(label_editable, header_font) + 6

    if L.get('show_name_capacity', True):
        name = (l['name'] or 'Battery pack')[:80]
        cap_text = '%s %s' % (capacity, unit)
        cap_w = _label_text_width(label_editable, cap_text, left_values_font)
        name_w = _label_text_width(label_editable, name, left_values_font)
        if name_w + cap_w + 12 <= text_max_w:
            label_editable.text((x0, y), name, (0, 0, 0), font=left_values_font)
            label_editable.text((x0 + text_max_w - cap_w, y), cap_text, (0, 0, 0), font=left_values_font)
            y += lh_body
        else:
            for line in _label_wrap_lines(label_editable, name, left_values_font, text_max_w):
                label_editable.text((x0, y), line, (0, 0, 0), font=left_values_font)
                y += lh_body
            label_editable.text((x0, y), cap_text, (0, 0, 0), font=left_values_font)
            y += lh_body

    y += 2
    if L.get('show_config_serial', True):
        if l['configuration']:
            row2 = '%s  %s' % (l['configuration'], serial)
        else:
            row2 = serial
        for line in _label_wrap_lines(label_editable, row2, left_values_font, text_max_w):
            label_editable.text((x0, y), line, (0, 0, 0), font=left_values_font)
            y += lh_body

    if L.get('show_esr', True):
        esr_txt = ('ESR: %s' % l['esr']) if l['esr'] is not None else 'ESR: —'
        for line in _label_wrap_lines(label_editable, esr_txt, left_values_font, text_max_w):
            label_editable.text((x0, y), line, (0, 0, 0), font=left_values_font)
            y += lh_body

    notes = (l['notes'] or '')[:120]
    if L.get('show_notes', True) and notes:
        y += 2
        for line in _label_wrap_lines(label_editable, notes, brand_font2, text_max_w):
            label_editable.text((x0, y), line, (0, 0, 0), font=brand_font2)
            y += _label_line_height(label_editable, brand_font2) + 2

    y += 4
    lh_small = _label_line_height(label_editable, brand_font2) + 3
    if L.get('show_mfg', True):
        label_editable.text((x0, y), 'Mfg: %s' % l['date'], (0, 0, 0), font=brand_font2)
        y += lh_small
    if L.get('show_custom_footer', True) and custom_field1:
        label_editable.text((x0, y), custom_field1, (0, 0, 0), font=brand_font2)
        y += lh_small
    if L.get('show_brand_url', True):
        label_editable.text((x0, y), 'deepcyclepower.com', (0, 0, 0), font=brand_font2)

    qr = qrcode.QRCode(
        version=1,
        box_size=int(L.get('qr_box_size', 9)),
        border=int(L.get('qr_border', 3)))
    qr.add_data('%s-C%s-%s' % (l['uuid'], capacity, unit))
    qr.make(fit=True)
    qr_img = qr.make_image(fill='black', back_color='white')
    qiw, qih = qr_img.size
    crop = min(qiw, qih, 400)
    qr_img = qr_img.crop((0, 0, crop, crop))
    qr_img = qr_img.resize((qr_size, qr_size))
    label.paste(qr_img, (qr_x, qr_y))

    buffered = BytesIO()
    label.save(buffered, format='JPEG')
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
        match = re.search(r'S0*(\d+)', acell.UUID)

        if match:
            # Extract the number part and convert it to an integer
            cserial = int(match.group(1))

        else:
            cserial = 0

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
        match = re.search(r'S0*(\d+)', acell.UUID)

        if match:
            # Extract the number part and convert it to an integer
            cserial = int(match.group(1))

        else:
            cserial = 0

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

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Prefetch
from .models import Projects, Device, Slot, Cells, CellTestData, PrinterSettings, Batteries
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .functions import scan_for_devices, add_new_cell, draw_dual_label, gather_label_data, draw_square_label, \
    draw_landscape_label, generate_uuid_for_cell, gather_label_cell_data, generate_battery_uuid, \
    draw_battery_pack_label
from .label_layout import (
    battery_layout_from_printer,
    cell_layout_from_printer,
    square_layout_from_printer,
    PREVIEW_BATTERY_LABEL_DICT,
    PREVIEW_BATTERY_CUSTOM_LINE,
)
from datetime import timedelta
import json
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import F
from mccprolib.api import MegacellCharger
from megacellcnc.tasks import dispatch_command, get_device_config, save_device_config
import msgpack
import base64
import re
import datetime
import pytz

import warnings

# Ignore all warnings
warnings.filterwarnings('ignore')
# Pandas (lazy-imported in get_history) performance noise
warnings.filterwarnings('ignore', module='pandas')


def index(request):
    devices = Device.objects.select_related('project', 'global_chemistry').order_by('id')
    devices_count = devices.count()
    projects = Projects.objects.all().prefetch_related(
        Prefetch('devices', queryset=Device.objects.select_related('global_chemistry').order_by('id'))
    )
    total_projects = Projects.objects.count()
    total_cells = Cells.objects.count()
    good_cells = Cells.objects.filter(capacity__gt=1000).count()
    online_devices = Device.objects.filter(status__iexact='online').count()

    context = {
        "page_title": "Dashboard",
        "devices": devices,
        "devices_count": devices_count,
        "projects": projects,
        "total_cells": total_cells,
        "good_cells": good_cells,
        "total_projects": total_projects,
        "online_devices": online_devices,
    }

    return render(request, 'megacellcnc/index.html', context)


@require_POST
def assign_device_project(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    device_id = data.get('device_id')
    project_id = data.get('project_id')

    device = get_object_or_404(Device, pk=device_id)
    old_pid = device.project_id

    if project_id in (None, '', 'unassigned'):
        device.project = None
    else:
        try:
            pid = int(project_id)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid project_id'}, status=400)
        device.project = get_object_or_404(Projects, pk=pid)

    device.save(update_fields=['project'])

    affected = {pid for pid in (old_pid, device.project_id) if pid is not None}
    for pid in affected:
        pr = Projects.objects.get(pk=pid)
        pr.DevCnt = Device.objects.filter(project=pr).count()
        pr.save(update_fields=['DevCnt'])

    return JsonResponse({
        'ok': True,
        'project_id': device.project_id,
        'project_name': device.project.Name if device.project else None,
    })

def settings(request):
    projects = Projects.objects.all()

    devices = Device.objects.all().order_by('id')
    devices_count = Device.objects.all().count()
    projects = Projects.objects.all()
    context = {
        "page_title": "Settings",
        "devices": devices,
        "devices_count": devices_count,
        "projects": projects
    }

    return render(request, 'megacellcnc/settings-page.html', context)


def new_project(request):

    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        cell_type = request.POST.get('cell_type')
        notes = request.POST.get('notes')

        new_project = Projects(Name=project_name, CellType=cell_type, Notes=notes, LastCellNumber=0, Status="Active", TotalCells=0)
        new_project.save()
        # Optionally, add a message to display on the next page
        print(project_name, cell_type, notes)
        messages.success(request, 'Project created successfully!')
        # # Redirect to a new URL or render the same template with context
        return redirect('/index/')
    else:
        # If it's a GET request, just render your form template
        context={
            "page_title":"New Project"
        }
        return render(request,'megacellcnc/forms/new-project.html',context)


def devices(request):

    if request.method == 'POST':
        print(" I received things to post")
        devices_details_str = request.POST.get('devicesDetails')

        # Parse the JSON string into a Python object
        try:
            devices_details = json.loads(devices_details_str)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        device_prefix = request.POST.get('device_prefix')
        project_id = request.POST.get('project')
        notes = request.POST.get('notes')
        added_devices = 0
        print("this is project id: %s" % project_id)
        try:
            project_instance = Projects.objects.get(id=project_id)
            print(project_instance)
        except (Projects.DoesNotExist, ValueError, TypeError):
            messages.error(request, 'Please select a valid project before adding devices.')
            return redirect('/devices/')

        print(devices_details)

        for device in devices_details:
            print(device)
            dev_name = "%s_%s" % (device_prefix, device["name"])

            # Use get_or_create to either fetch the existing device with the given MAC or create a new one
            device_obj, created = Device.objects.get_or_create(
                mac=device["mac"],  # Look up by MAC address
                defaults={  # Provide the default values for creation
                    'type': device["dev_type"],
                    'name': dev_name,
                    'ip': device["ip"],
                    'runtime': timedelta(0),
                    'project': project_instance
                }
            )

            # After adding the device, count the devices related to the project
            device_count = Device.objects.filter(project=project_instance).count()

            if created:
                print("New device added:", device_obj)
                added_devices += 1

                # Create and assign the specified number of slots to the newly created device
                slot_count = int(device.get("slot_count", 0))  # Default to 0 if "slot_count" is not provided
                print("This is slot count: %s" % slot_count)
                for slot_num in range(1, slot_count + 1):  # Starting from 1 to slot_count
                    Slot.objects.create(device=device_obj, slot_number=slot_num)
                    # Optionally add other default slot parameters if needed

                with transaction.atomic():  # Ensure atomicity of the update operation
                    project_instance.DevCnt = device_count
                    project_instance.save()

            else:
                print("Device already exists:", device_obj)

        print(devices_details, device_prefix, project_id, notes)
        if added_devices > 1:
            messages.success(request, '%s Devices added successfully!' % added_devices)

        if added_devices == 1:
            messages.success(request, 'Device added successfully!')

            # Redirect to a new URL or render the same template with context
        return redirect('/devices/')

    else:
        devices = Device.objects.all().order_by('id')
        devices_count = Device.objects.all().count()
        projects = Projects.objects.all()
        context = {
            "page_title":"Devices",
            "devices": devices,
            "devices_count": devices_count,
            "projects": projects
        }
        return render(request, 'megacellcnc/devices.html', context)


def add_cell(request):
    if request.method == 'POST':
        project_id = int(request.POST['project_id'])
        uuid = generate_uuid_for_cell(project_id)

        cell_type = request.POST['cell_type']
        device_type = request.POST['device_type']
        voltage = request.POST['voltage']
        capacity = request.POST['capacity']
        esr = request.POST['esr']
        esr_ac = request.POST['esr_ac']
        min_voltage = request.POST['min_voltage']
        store_voltage = request.POST['store_voltage']
        max_voltage = request.POST['max_voltage']
        testing_current = request.POST['testing_current']
        discharge_mode = request.POST['discharge_mode']
        project_instance = get_object_or_404(Projects, id=project_id)

        # Create and save the new cell
        new_cell = Cells(
            project=project_instance,
            UUID=uuid,
            cell_type=cell_type,
            device_ip="0.0.0.0",
            device_mac="00:00:00:00:00",
            device_type=device_type,
            device_slot=0,
            voltage=voltage,
            capacity=capacity,
            esr=esr,
            esr_ac=esr_ac,
            test_duration=0,
            charge_duration=0,
            discharge_duration=0,
            cycles_count=1,
            temp_before_test=0,
            avg_temp_charging=0,
            avg_temp_discharging=0,
            max_temp_charging=0,
            max_temp_discharging=0,
            min_voltage=min_voltage,
            max_voltage=max_voltage,
            store_voltage=store_voltage,
            testing_current=testing_current,
            discharge_mode=discharge_mode,
            status="N.A",
            insertion_date=timezone.now(),
            removal_date=timezone.now(),
            available='Yes'
        )
        new_cell.save()
        project_instance.update_total_cells()

        return JsonResponse({'message': 'Cell added successfully'}, status=200)


def delete_cells(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            cell_ids = data.get('cell_ids')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if len(cell_ids) > 0:
            count, _ = Cells.objects.filter(id__in=cell_ids).delete()
        else:
            messages.error(request, 'No Cell Selected')
            return JsonResponse({'error': 'No Cell selected'}, status=400)

        if len(cell_ids) == 1:
            messages.success(request, '%s Cell removed successfully!' % len(cell_ids))
        elif len(cell_ids) > 1:
            messages.success(request, '%s Cells removed successfully!' % len(cell_ids))

        # Device.objects.filter(id__in=device_ids).delete()
        # Redirect to a success page or back to the device list
        return JsonResponse({'message': f'Successfully deleted {len(cell_ids)} cells.'})
        # return HttpResponseRedirect(reverse('devices'))
    # Handle other HTTP methods or return an error response


@require_http_methods(["POST"])
def delete_batteries(request):
    """
    Delete battery packs. Optional cell_disposition:
    - release: unassign cells, set available=Yes
    - delete_cells: delete cell records
    - keep_unavailable: unassign cells, set available=No
    """
    try:
        data = json.loads(request.body)
        battery_ids = data.get('battery_ids')
        cell_disposition = data.get('cell_disposition', 'release')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not battery_ids:
        return JsonResponse({'error': 'No batteries selected'}, status=400)

    if cell_disposition not in ('release', 'delete_cells', 'keep_unavailable'):
        return JsonResponse({'error': 'Invalid cell_disposition'}, status=400)

    try:
        ids = [int(x) for x in battery_ids]
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid battery ids'}, status=400)

    with transaction.atomic():
        for bid in ids:
            bat = Batteries.objects.filter(id=bid).first()
            if not bat:
                continue
            qs = Cells.objects.filter(battery=bat)
            if cell_disposition == 'delete_cells':
                qs.delete()
            elif cell_disposition == 'keep_unavailable':
                qs.update(battery=None, bat_position='', available='No')
            else:
                qs.update(battery=None, bat_position='', available='Yes')
            bat.delete()

    return JsonResponse({'message': f'Successfully deleted {len(ids)} battery pack(s).'})


@require_http_methods(["GET"])
def battery_detail(request, battery_id):
    battery = get_object_or_404(Batteries, id=battery_id)
    return JsonResponse({
        'id': battery.id,
        'name': battery.name,
        'notes': battery.notes or '',
        'pack_esr': battery.pack_esr,
        'manufacturing_date': battery.manufacturing_date.isoformat() if battery.manufacturing_date else None,
        'uuid': battery.UUID,
        'capacity': battery.capacity,
        'series': battery.series,
        'parallel': battery.parallel,
    })


@require_http_methods(["POST"])
def update_battery(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    battery_id = data.get('battery_id')
    battery = get_object_or_404(Batteries, id=battery_id)

    if 'name' in data:
        battery.name = (data.get('name') or '').strip()[:150]
    if 'notes' in data:
        battery.notes = (data.get('notes') or '')
    if 'pack_esr' in data:
        pe = data.get('pack_esr')
        if pe in (None, ''):
            battery.pack_esr = None
        else:
            try:
                battery.pack_esr = float(pe)
            except (TypeError, ValueError):
                return JsonResponse({'status': 'error', 'message': 'Invalid pack ESR'}, status=400)
    if 'manufacturing_date' in data:
        raw = data.get('manufacturing_date')
        if raw:
            d = parse_date(str(raw))
            battery.manufacturing_date = d
        else:
            battery.manufacturing_date = None

    battery.save()
    return JsonResponse({'status': 'success', 'message': 'Battery pack updated.'})


@require_http_methods(["POST"])
def print_battery_pack_label(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    is_demo = int(data.get('isDemo', 0))
    battery_id = data.get('batteryId')

    printer = PrinterSettings.objects.all().first()
    if not printer:
        return JsonResponse({'error': 'No printer configured'}, status=400)

    if is_demo:
        battery = Batteries.objects.order_by('-id').first()
        if not battery:
            return JsonResponse({'error': 'No battery packs to preview'}, status=400)
    else:
        if not battery_id:
            return JsonResponse({'error': 'batteryId required'}, status=400)
        battery = get_object_or_404(Batteries, id=battery_id)

    custom = printer.CustomField1 or ''
    label = draw_battery_pack_label(battery, custom, battery_layout_from_printer(printer))

    return JsonResponse({
        'label': f'{label}',
        'message': 'Label generated',
    })


def get_cells(request):
    project_id = request.GET.get('project_id')
    for_pack_battery_id = request.GET.get('for_pack_battery_id')

    exclude_uuids = []
    if for_pack_battery_id:
        try:
            bid = int(for_pack_battery_id)
            bat = Batteries.objects.filter(id=bid).first()
            if bat and bat.draft_json:
                exclude_uuids = [
                    x['cellId'] for x in bat.draft_json.get('cellsData', [])
                    if x.get('cellId')
                ]
        except (TypeError, ValueError):
            pass

    if project_id == 'all':
        cells = Cells.objects.filter(available="Yes", battery__isnull=True)
    else:
        cells = Cells.objects.filter(project_id=project_id, available="Yes", battery__isnull=True)

    if exclude_uuids:
        cells = cells.exclude(UUID__in=exclude_uuids)

    cells_data = []
    for cell in cells:
        match = re.search(r'-S(\d+)', cell.UUID)
        if match:
            serial_number = int(match.group(1))
            cdata = {
                'id': serial_number,
                'capacity': cell.capacity,
                'uuid': cell.UUID,
                'esr': cell.esr,
            }
            cells_data.append(cdata)

    return JsonResponse({'cells': cells_data})


def get_battery_cells(request):
    bat_id_str = request.GET.get('bat_id')
    if not bat_id_str:
        return JsonResponse({'error': 'bat_id is required'}, status=400)
    battery_id = int(bat_id_str)

    battery = get_object_or_404(Batteries, id=battery_id)
    cells_data = []
    assigned = list(battery.battery_cells.all())
    if assigned:
        for cell in assigned:
            match = re.search(r'-S(\d+)', cell.UUID)
            if match:
                serial_number = int(match.group(1))
                cdata = {
                    'id': serial_number,
                    'capacity': cell.capacity,
                    'uuid': cell.UUID,
                    'bat_position': cell.bat_position,
                    'esr': cell.esr,
                }
                cells_data.append(cdata)
    elif battery.draft_json:
        for item in battery.draft_json.get('cellsData', []) or []:
            cell_uuid = item.get('cellId')
            slot_id = item.get('slotId')
            if not cell_uuid:
                continue
            try:
                cell = Cells.objects.get(UUID=cell_uuid)
            except Cells.DoesNotExist:
                continue
            match = re.search(r'-S(\d+)', cell.UUID)
            if match:
                serial_number = int(match.group(1))
                cdata = {
                    'id': serial_number,
                    'capacity': cell.capacity,
                    'uuid': cell.UUID,
                    'bat_position': slot_id,
                    'esr': cell.esr,
                }
                cells_data.append(cdata)

    draft_project_id = None
    if battery.draft_json:
        draft_project_id = battery.draft_json.get('projectId')
    if draft_project_id is None and assigned:
        draft_project_id = assigned[0].project_id

    return JsonResponse({
        'cells': cells_data,
        'draftProjectId': draft_project_id,
        'packStatus': battery.status,
        'series': battery.series,
        'parallel': battery.parallel,
    })


def database(request):

    projects = Projects.objects.all()
    project_id = request.GET.get('project')

    if project_id == 'all' or project_id is None:
        cells = Cells.objects.all().order_by('id')
        selected_project_name = "All"
    else:
        cells = Cells.objects.filter(project__id=project_id).order_by().order_by('id')
        selected_project_name = Projects.objects.get(id=project_id).Name

    context = {
        "page_title":"Devices",
        "cells": cells,
        "projects": projects,
        'selected_project_name': selected_project_name
    }
    return render(request, 'megacellcnc/database.html', context)


def batteries(request):
    projects = Projects.objects.all()
    projects_data = [{'id': prj.id, 'name': prj.Name} for prj in projects]
    batteries = Batteries.objects.annotate(cells_count=Count('battery_cells'))
    for battery in batteries:
        battery.series_parallel = (battery.series or 0) * (battery.parallel or 0)

    context = {
        "page_title":"Batteries",
        "batteries": batteries,
        "projects": json.dumps(projects_data)
    }
    return render(request, 'megacellcnc/batteries.html', context)


def add_battery(request):
    if request.method != 'POST':
        return redirect(reverse('megacellcnc:batteries'))

    battery_name = (request.POST.get('battery_name') or '').strip()
    try:
        series = int(request.POST.get('series', '0'))
        parallel = int(request.POST.get('parallel', '0'))
    except (TypeError, ValueError):
        messages.error(request, 'Series and parallel must be whole numbers.')
        return redirect(reverse('megacellcnc:batteries'))

    if not battery_name or series < 1 or parallel < 1:
        messages.error(request, 'Battery name is required; series and parallel must be at least 1.')
        return redirect(reverse('megacellcnc:batteries'))

    uuid = generate_battery_uuid()

    new_battery = Batteries(
        name=battery_name,
        UUID=uuid,
        series=series,
        parallel=parallel,
        cell_type='',
        voltage=0,
        capacity=0,
        status="Created",
        available="Yes",
    )
    new_battery.save()
    messages.success(request, f'Battery "{battery_name}" created ({series}S{parallel}P).')
    return redirect(reverse('megacellcnc:batteries'))


@require_http_methods(["POST"])  # Only allow POST requests
def save_battery_configuration(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    battery_id = data.get('batteryId')
    cells_data = data.get('cellsData') or []
    is_draft = bool(data.get('isDraft'))
    project_id = data.get('projectId')

    try:
        battery = Batteries.objects.get(id=battery_id)
    except Batteries.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Battery not found'}, status=404)

    series = battery.series or 0
    parallel = battery.parallel or 0
    required = series * parallel

    if not is_draft and required > 0 and len(cells_data) != required:
        return JsonResponse({
            'status': 'error',
            'message': (
                f'A complete pack requires exactly {required} cells in slots '
                f'(you have {len(cells_data)}). Use “Save draft” for incomplete progress.'
            ),
        }, status=400)

    if not is_draft:
        for item in cells_data:
            cell_uuid = item.get('cellId')
            try:
                c = Cells.objects.get(UUID=cell_uuid)
            except Cells.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Cell not found'}, status=404)
            if c.battery_id and c.battery_id != battery.id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'One or more cells are already assigned to another pack.',
                }, status=400)

    try:
        with transaction.atomic():
            battery = Batteries.objects.select_for_update().get(id=battery_id)
            Cells.objects.filter(battery=battery).update(
                battery=None, bat_position='', available='Yes'
            )

            if is_draft:
                battery.draft_json = {
                    'projectId': project_id,
                    'cellsData': cells_data,
                }
                battery.status = 'Draft'
                battery.save(update_fields=['draft_json', 'status'])
            else:
                battery.draft_json = None
                battery.status = 'Complete'
                battery.save(update_fields=['draft_json', 'status'])

                for item in cells_data:
                    cell_uuid = item['cellId']
                    slot_id = item['slotId']
                    cell = Cells.objects.select_for_update().get(UUID=cell_uuid)
                    cell.battery = battery
                    cell.bat_position = slot_id
                    cell.available = "No"
                    cell.save()

    except Cells.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Cell not found'}, status=404)
    except KeyError as e:
        return JsonResponse({'status': 'error', 'message': f'Missing field: {e}'}, status=400)

    if is_draft:
        return JsonResponse({
            'status': 'success',
            'message': 'Draft saved. Cells are not assigned in the database until you finalize.',
        })
    return JsonResponse({
        'status': 'success',
        'message': 'Pack finalized — cells assigned to the battery.',
    })

def device_slots(request):
    dev_id = request.GET.get('dev_id')
    device = get_object_or_404(Device, id=dev_id)
    slots = device.slots.all().order_by('slot_number')
    slots_count = device.slots.all().count()
    context = {
        "page_title": "Device",
        "device": device,
        "slots": slots,
        "slots_count": slots_count
    }

    return render(request, 'megacellcnc/device-slots.html', context)


@require_POST
@csrf_exempt
def handle_device_action(request):

    action_map = {
        "charge": "ach",
        "discharge": "adc",
        "store_charge": "asc",
        "esr": "esr",
        "stop": "sc",
        "stop_macro": "stop",
        "dispose": "dsp",
        "macro": "mCap"
    }

    data = json.loads(request.body)
    action = data.get('action')
    slots_number = data.get('slots_number')
    cell_map = [int(x) - 1 for x in slots_number]

    deviceId = data.get('deviceId')

    try:
        device = Device.objects.get(id=deviceId)
    except Device.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)



    cells = []

    for cell in cell_map:

        if device.type == "MCC" and action == "macro":
            cells.append({"CiD": cell, "CmD": "act"})
            print("This is a MCC device")
            continue

        cells.append({"CiD": cell, "CmD": action_map.get(action, action)})

    request_data = {"cells": cells}

    if "macro" in action and (device.type == "MCCPro" or device.type == "MCCReg"):
        action_type = "macro"
    else:
        action_type = "regular"

    try:
        result = dispatch_command.delay(data, request_data, action_type)
        if hasattr(result, 'get'):
            result.get(timeout=30)
    except Exception as e:
        return JsonResponse({'error': f'Command failed: {e}'}, status=500)

    return JsonResponse({'message': f'{action.capitalize()} action submitted for selected devices.'})


def get_updated_slots(request, device_id):
    # Fetch the device and its slots
    device = get_object_or_404(Device, id=device_id)

    slots = device.slots.all()

    slots_info = []

    for slot in slots:
        slot_info = {
            'slot_number': slot.slot_number,
            'voltage': slot.voltage,
            'current': slot.current,
            'esr': slot.esr,
            'capacity': slot.capacity,
            'charge_capacity': slot.charge_capacity,
            'state': slot.state,
            'action_running_time': slot.action_running_time,
            'completed_cycles': slot.completed_cycles,
            'discharge_cycles_set': slot.discharge_cycles_set,
            'temperature': slot.temperature,
            'max_volt': slot.max_volt,
            'store_volt': slot.store_volt,
            'min_volt': slot.min_volt,
            'active_cell_uuid': "",
            'active_cell_type': ""
        }

        if slot.active_cell:
            match = re.search(r'-S(\d+)', slot.active_cell.UUID)
            serial_number = int(match.group(1)) if match else 0

            slot_info.update({
                'active_cell_uuid': serial_number,
                'active_cell_type': slot.active_cell.cell_type,
            })

        slots_info.append(slot_info)
    return JsonResponse(slots_info, safe=False)


def get_project_slots(request, project_id):
    devices = Device.objects.filter(project__id=project_id).prefetch_related('slots__chemistry')

    # Serialize devices and their slots into a list of dictionaries
    devices_data = []
    for device in devices:
        slots_data = []
        for slot in device.slots.all().order_by('slot_number'):

            slot_info = {
                'slot_number': slot.slot_number,
                'voltage': slot.voltage,
                'current': slot.current,
                'esr': slot.esr,
                'capacity': slot.capacity,
                'charge_capacity': slot.charge_capacity,
                'state': slot.state,
                'action_running_time': slot.action_running_time,
                'completed_cycles': slot.completed_cycles,
                'discharge_cycles_set': slot.discharge_cycles_set,
                'temperature': slot.temperature,
                'max_volt': slot.max_volt,
                'store_volt': slot.store_volt,
                'min_volt': slot.min_volt,
                'active_cell_uuid': "",
                'active_cell_type': ""
            }

            if slot.active_cell:
                match = re.search(r'-S(\d+)', slot.active_cell.UUID)
                serial_number = int(match.group(1)) if match else 0
                slot_info.update({
                    'active_cell_uuid': serial_number,
                    'active_cell_type': slot.active_cell.cell_type,
                })

            slots_data.append(slot_info)

        devices_data.append({
            "id": device.id,
            "name": device.name,
            "slots": slots_data,
        })

    return JsonResponse(devices_data, safe=False)


def delete_devices(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            device_ids = data.get('device_ids')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if len(device_ids) > 0:
            count, _ = Device.objects.filter(id__in=device_ids).delete()
        else:
            messages.error(request, 'No Device Selected')
            return JsonResponse({'error': 'No device selected'}, status=400)

        if len(device_ids) == 1:
            messages.success(request, '%s Device removed successfully!' % len(device_ids))
        elif len(device_ids) > 1:
            messages.success(request, '%s Devices removed successfully!' % len(device_ids))

        # Device.objects.filter(id__in=device_ids).delete()
        # Redirect to a success page or back to the device list
        return JsonResponse({'message': f'Successfully deleted {len(device_ids)} devices.'})
        # return HttpResponseRedirect(reverse('devices'))
    # Handle other HTTP methods or return an error response


def new_device(request):

    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        cell_type = request.POST.get('cell_type')
        notes = request.POST.get('notes')

        new_project = Projects(Name=project_name, CellType=cell_type, Notes=notes, LastCellNumber=0, Status="Active", TotalCells=0)
        new_project.save()
        # Optionally, add a message to display on the next page
        print(project_name, cell_type, notes)
        messages.success(request, 'Project created successfully!')
        # # Redirect to a new URL or render the same template with context
        return redirect('/index/')
    else:
        # If it's a GET request, just render your form template
        context={
            "page_title":"New Project"
        }
        return render(request,'megacellcnc/forms/new-device.html',context)


def edit_device(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            device_id = int(payload.get('device_id'))
        except (json.JSONDecodeError, TypeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        device = get_object_or_404(Device, id=device_id)
        slots_count = device.slots.count()
        dev_type = (device.type or "").strip()

        try:
            result_async = get_device_config.delay(device_id)
            raw = result_async.get(timeout=120)
        except Exception as exc:
            return JsonResponse({'error': f'Could not reach device: {exc}'}, status=502)

        if raw is None or not isinstance(raw, (tuple, list)) or len(raw) != 3:
            return JsonResponse({'error': 'Invalid response from device config service'}, status=502)

        task_result, chems, firmware_version = raw

        if not task_result:
            return JsonResponse({'error': 'Device is offline or unreachable'}, status=503)

        body = None

        try:
            if dev_type == "MCC" and isinstance(task_result, dict):
                body = {"dev_type": dev_type, "max_charge_volt": round(task_result["MaV"], 2),
                        "store_volt": round(task_result["StV"], 2),
                        "discharge_volt": round(task_result["MiV"], 2), "max_temp": round(task_result["MaT"], 2),
                        "discharge_cycles": task_result["DiC"], "firmware": task_result["FwV"],
                        "discharge_current": int(task_result["DiR"]), "charging_current": 1000,
                        "charging_timeout": task_result["McH"], "device_name": device.name, "slots_count": slots_count,
                        "chems": chems, "max_capacity": 5000, "pre_charge_current": 0,
                        "term_charging_current": 0, "discharge_resistance": 0,
                        "discharge_mode": 0, "max_low_volt_recovery_time": 120}

            elif dev_type in ("MCCPro", "MCCReg") and task_result is not None:
                if isinstance(task_result, dict):
                    return JsonResponse({
                        'error': 'Expected packed MCCPro/MCCReg config from device, got JSON. Check device API / DB type.'
                    }, status=502)
                try:
                    if isinstance(task_result, str):
                        raw_chem = base64.b64decode(task_result)
                    elif isinstance(task_result, (bytes, bytearray)):
                        raw_chem = bytes(task_result)
                    else:
                        raise TypeError(f"Unexpected payload type {type(task_result)}")
                except Exception as exc:
                    return JsonResponse({
                        'error': f'Invalid chemistry payload from worker (expected base64 MessagePack): {exc}'
                    }, status=502)
                dev_data = msgpack.unpackb(raw_chem, raw=False)

                body = {"dev_type": dev_type, "max_charge_volt": round(dev_data[2] / 1000, 2),
                        "store_volt": round(dev_data[4] / 1000, 2),
                        "discharge_volt": round(dev_data[3] / 1000, 2), "max_temp": round(dev_data[12], 2),
                        "discharge_cycles": dev_data[15], "firmware": firmware_version,
                        "discharge_current": int(dev_data[9]), "charging_current": dev_data[6],
                        "charging_timeout": dev_data[14], "device_name": device.name, "slots_count": slots_count,
                        "chems": chems, "max_capacity": dev_data[5], "pre_charge_current": dev_data[7],
                        "term_charging_current": dev_data[8], "discharge_resistance": dev_data[10],
                        "discharge_mode": dev_data[11], "max_low_volt_recovery_time": dev_data[13]}
        except Exception as exc:
            return JsonResponse({'error': f'Failed to parse device configuration: {exc}'}, status=502)

        if body is None:
            return JsonResponse({
                'error': f'Unsupported device type "{dev_type}" or config format does not match (MCC / MCCPro / MCCReg).'
            }, status=422)

        # Frontend always JSON.parse(chems) — must be a non-empty serialized array string
        _c = body.get("chems")
        if _c is None or (isinstance(_c, str) and not _c.strip()):
            body["chems"] = "[]"
        elif not isinstance(_c, str):
            body["chems"] = json.dumps(_c) if _c is not None else "[]"

        return JsonResponse(body, safe=False)


def save_device_settings(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            device_id = int(data.get('device_id'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        save_device_config.delay(device_id, data)
        return JsonResponse({'message': f'Successfully saved device info.'})


def save_printer_settings(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            printerName = data.get('printerName') or ''
            labelWidth = float(data.get('labelWidth') or 0)
            labelHeight = float(data.get('labelHeight') or 0)
            labelRotation = int(data.get('labelRotation') or 0)
            dualLabel = int(data.get('dualLabel') or 0)
            printerHost = data.get('printerHost')
            customField1 = data.get('customField1')
            label_shape = data.get('label_shape')

            printer_settings, created = PrinterSettings.objects.get_or_create(
               id=1
            )

            printer_settings.PrinterName = printerName
            printer_settings.PrinterHost = printerHost
            printer_settings.IsDualLabel = dualLabel
            printer_settings.LabelWidth = labelWidth
            printer_settings.LabelHeight = labelHeight
            printer_settings.LabelRotation = labelRotation
            printer_settings.CustomField1 = customField1
            printer_settings.LabelShape = label_shape

            cell_l = data.get('cellLabelLayoutJson')
            bat_l = data.get('batteryLabelLayoutJson')
            sq_l = data.get('squareLabelLayoutJson')
            if cell_l is not None:
                printer_settings.CellLabelLayoutJson = cell_l if isinstance(cell_l, str) else json.dumps(cell_l)
            if bat_l is not None:
                printer_settings.BatteryLabelLayoutJson = bat_l if isinstance(bat_l, str) else json.dumps(bat_l)
            if sq_l is not None:
                printer_settings.SquareLabelLayoutJson = sq_l if isinstance(sq_l, str) else json.dumps(sq_l)

            printer_settings.save()

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'message': 'Settings saved successfully.'})


def get_printer_settings(request):

    if request.method == "GET":
        printer_data = {}

        # printer = get_object_or_404(PrinterSettings, id=1)
        printer = PrinterSettings.objects.all().first()

        if printer:
            print("Printer exists")

            printer_data = {
                'printerName': printer.PrinterName,
                'printerHost': printer.PrinterHost,
                'dualLabel': printer.IsDualLabel,
                'labelWidth': printer.LabelWidth,
                'labelHeight': printer.LabelHeight,
                'labelRotation': printer.LabelRotation,
                'customField1': printer.CustomField1,
                'label_shape': printer.LabelShape,
                'cellLabelLayoutJson': getattr(printer, 'CellLabelLayoutJson', None) or '{}',
                'squareLabelLayoutJson': getattr(printer, 'SquareLabelLayoutJson', None) or '{}',
                'batteryLabelLayoutJson': getattr(printer, 'BatteryLabelLayoutJson', None) or '{}',
            }


            # data = json.loads(request.body)
            # printerName = data.get('printerName')
            # labelWidth = float(data.get('labelWidth'))
            # labelHeight = float(data.get('labelHeight'))

        # save_device_config.delay(device_id, data)
        return JsonResponse(printer_data, safe=False)


def print_label(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            isDemo = int(data.get('isDemo'))
            deviceId = data.get('deviceId')
            slots = data.get('slots')
            printer = PrinterSettings.objects.all().first()

            # Step 1: Ensure slots is a list
            if isinstance(slots, str):
                slots = [slots]  # Convert single string to list

            # Step 2: Convert all elements in the list to integers
            slots = [int(slot) for slot in slots]

            if printer:

                # Regular Printing
                if printer.IsDualLabel:

                    if isDemo:
                        label = draw_dual_label([])

                        response_data = {
                            "label": f"{label}"
                            # Ensure the format matches the format used in saving the image
                        }
                        return JsonResponse(response_data)

                    if deviceId != -1:
                        label_data = gather_label_data(deviceId, slots)
                    else:
                        label_data = gather_label_cell_data(slots)
                    label = draw_dual_label(label_data)

                    response_data = {
                        "label": f"{label}"
                    }
                    return JsonResponse(response_data)

                else:

                    if isDemo:

                        if printer.LabelShape == "square":
                            label = draw_square_label([], printer.CustomField1, square_layout_from_printer(printer))
                        else:
                            label = draw_landscape_label([], printer.CustomField1, cell_layout_from_printer(printer))

                        response_data = {
                            "label": f"{label}"
                            # Ensure the format matches the format used in saving the image
                        }
                        return JsonResponse(response_data)

                    if deviceId != -1:
                        label_data = gather_label_data(deviceId, slots)
                    else:
                        label_data = gather_label_cell_data(slots)

                    if printer.LabelShape == "square":
                        label = draw_square_label(label_data, printer.CustomField1, square_layout_from_printer(printer))
                    else:
                        label = draw_landscape_label(label_data, printer.CustomField1, cell_layout_from_printer(printer))

                    response_data = {
                        "label": f"{label}"
                    }
                    return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)


@require_http_methods(["POST"])
def preview_label_layout(request):
    """Live preview for settings QR label editor (cell / battery); uses demo data."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    kind = data.get('kind')
    layout = data.get('layout') or {}
    printer = PrinterSettings.objects.all().first()
    custom = (printer.CustomField1 if printer else '') or ''
    if not custom.strip():
        custom = PREVIEW_BATTERY_CUSTOM_LINE

    if kind == 'battery':
        label = draw_battery_pack_label(PREVIEW_BATTERY_LABEL_DICT, custom, layout)
    elif kind == 'cell':
        label = draw_landscape_label([], custom, layout)
    elif kind == 'square':
        label = draw_square_label([], custom, layout)
    else:
        return JsonResponse({'error': 'kind must be battery, cell, or square'}, status=400)

    return JsonResponse({'label': label, 'message': 'ok'})


def save_cell(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            device_id = int(data.get('device_id'))
            slot_id = int(data.get('slot_id'))

            device = get_object_or_404(Device, id=device_id)
            slot = Slot.objects.filter(device_id=device_id, slot_number=slot_id).first()

            if not slot.saved:
                add_new_cell(device, slot)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        return JsonResponse({'message': f'Successfully saved cell from slot %s' % slot_id})


def get_history(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            slot_id = data.get('slot_id')
            timeframe = data.get('timeframe')
            cell_id = -1

            if device_id == -1:
                cell_id = data.get('cell_id')

            if device_id is None or slot_id is None:
                return JsonResponse({'error': 'Missing device_id or slot_id'}, status=400)

            device_id = int(device_id)
            slot_id = int(slot_id)
            cell_id = int(cell_id)

            # Assuming you have a function or method to get the slot object.
            # Replace `Slot.objects.filter(...).first()` with your actual query method.

            if cell_id == -1:

                try:
                    slot = Slot.objects.get(device_id=device_id, slot_number=slot_id)
                except ObjectDoesNotExist:
                    return JsonResponse({'error': 'Slot not found'}, status=404)

                cell = slot.active_cell

            else:

                try:
                    cell = Cells.objects.get(id=cell_id)
                except ObjectDoesNotExist:
                    return JsonResponse({'error': 'Cell not found'}, status=404)

            if cell:
                cell_test_data = CellTestData.objects.filter(cell=cell).order_by('timestamp')
                if len(cell_test_data) == 0:
                    response_data = {'labels': [], 'volts': [], 'current': [],
                                     'cap': []}
                    return JsonResponse(response_data)
                # labels = []
                # volt_data = []
                # current_data = []
                # capacity_data = []
                #
                # for test_data in cell_test_data:
                #     labels.append(test_data.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                #     volt_data.append(test_data.voltage)
                #     current_data.append(test_data.current)
                #     capacity_data.append(test_data.capacity)

                import pandas as pd

                df = pd.DataFrame.from_records(
                    [
                        {
                            'timestamp': test_data.timestamp,
                            'voltage': test_data.voltage,
                            'current': test_data.current,
                            'temperature': test_data.temperature
                        }
                        for test_data in cell_test_data
                    ]
                )

                # Get the local timezone
                local_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
                # Set 'timestamp' as the DataFrame index and convert it to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['timestamp'] = df['timestamp'].dt.tz_convert(local_timezone)
                df.set_index('timestamp', inplace=True)

                # History charts: full series resampled to bucket size (mean).
                # "5m" = fast default (5-minute buckets). "rt_10s" = realtime window only (last 30 min).

                if timeframe == "5m":
                    resampled_df = df.resample("5min").mean()
                elif timeframe == "1m":
                    resampled_df = df.resample("1min").mean()
                elif timeframe == "30s":
                    resampled_df = df.resample("30s").mean()
                elif timeframe == "10s":
                    resampled_df = df.resample("10s").mean()
                elif timeframe == "rt_10s":
                    resampled_df = df.resample("10s").mean()
                    # Explicit window (pandas .last() on DataFrame is brittle across versions)
                    if len(resampled_df.index) > 0:
                        end_ts = resampled_df.index.max()
                        start_ts = end_ts - pd.Timedelta(minutes=30)
                        resampled_df = resampled_df.loc[resampled_df.index >= start_ts]
                else:
                    resampled_df = df.resample("5min").mean()

                # Keep rows that have the main signals; fill temp NaNs from resample gaps
                resampled_df = resampled_df.dropna(subset=["voltage", "current"], how="any")
                if "temperature" in resampled_df.columns:
                    resampled_df["temperature"] = (
                        resampled_df["temperature"].ffill().bfill().fillna(0)
                    )
                cleaned_df = resampled_df.dropna()
                cleaned_df["voltage"] = cleaned_df["voltage"].round(2)
                cleaned_df["current"] = cleaned_df["current"].round(2)
                cleaned_df["temperature"] = cleaned_df["temperature"].round(0).astype(int)
                # Now, extract the resampled data back to lists
                labels = cleaned_df.index.strftime('%Y-%m-%d %H:%M:%S').tolist()
                volt_data = cleaned_df['voltage'].tolist()
                current_data = cleaned_df['current'].tolist()
                temp_data = cleaned_df['temperature'].tolist()

                response_data = {'labels': labels, 'volts': volt_data, 'current': current_data, 'temp': temp_data}
                return JsonResponse(response_data)

            else:
                return JsonResponse({'error': 'No active cell in the selected slot'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Invalid device_id or slot_id'}, status=400)
        except Exception as e:
            print(str(e))
            return JsonResponse({'error': str(e)}, status=500)


def project(request):

    if request.method == 'POST':
        print(" I received things to post")
        project_name = request.POST.get('project_name')
        cell_type = request.POST.get('cell_type')
        notes = request.POST.get('notes')

        new_project = Projects(Name=project_name, CellType=cell_type, Notes=notes, LastCellNumber=0, Status="Active", TotalCells=0)
        new_project.save()
        # Optionally, add a message to display on the next page
        print(project_name, cell_type, notes)
        messages.success(request, 'Project created successfully!')
        # # Redirect to a new URL or render the same template with context
        return redirect('/project/')

    else:
        projects = Projects.objects.all()
        projects_count = Projects.objects.all().count()
        context = {
            "page_title":"Projects",
            "projects_count": projects_count,
            "projects": projects
        }
        return render(request, 'megacellcnc/project.html', context)


def project_details(request):

    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        cell_type = request.POST.get('cell_type')
        notes = request.POST.get('notes')

        new_project = Projects(Name=project_name, CellType=cell_type, Notes=notes, LastCellNumber=0, Status="Active", TotalCells=0)
        new_project.save()
        # Optionally, add a message to display on the next page
        print(project_name, cell_type, notes)
        messages.success(request, 'Project created successfully!')
        # # Redirect to a new URL or render the same template with context
        return redirect('/project/')

    else:

        proj_id = request.GET.get('proj_id')
        project = get_object_or_404(Projects, pk=proj_id)

        # Prepare a queryset for slots, ordered by slot_number
        slots_queryset = Slot.objects.order_by('slot_number')

        # Use Prefetch to apply the custom queryset for slots to the devices query
        devices = Device.objects.filter(project=project).prefetch_related(
            Prefetch('slots', queryset=slots_queryset)
        )
        devices = devices.order_by("id")
        device_count = devices.count()
        context = {
            "page_title":"Projects Details",
            'project': project,
            'devices': devices,
            'device_count': device_count
        }
        return render(request, 'megacellcnc/project-details.html', context)


def scan_devices(request):
    if request.method == "POST":
        ip_from = request.POST.get('ip_from')
        ip_to = request.POST.get('ip_to')
        manual_ip = request.POST.get('device_manual_ip')

        # Use the IP range in your scanning function
        devices_list = scan_for_devices(ip_from, ip_to, manual_ip)

        # Return the list of devices as JSON (or render a template with the context)
        return JsonResponse({'devices': devices_list})

    # If not a POST request, or you need to show the form again
    return render(request, 'megacellcnc/devices.html')






def employee(request):
    context={
        "page_title":"Employee"
    }
    return render(request,'megacellcnc/employee.html',context)

def core_hr(request):
    context={
        "page_title":"Core HR"
    }
    return render(request,'megacellcnc/core-hr.html',context)

def finance(request):
    context={
        "page_title":"Finance"
    }
    return render(request,'megacellcnc/finance.html',context)

def task(request):
    context={
        "page_title":"Tasks"
    }
    return render(request,'megacellcnc/task.html',context)

def task_summary(request):
    context={
        "page_title":"Task Summary"
    }
    return render(request,'megacellcnc/task-summary.html',context)

def performance(request):
    context={
        "page_title":"Performance"
    }
    return render(request,'megacellcnc/performance.html',context)




def reports(request):
    context={
        "page_title":"Reports"
    }
    return render(request,'megacellcnc/reports.html',context)

def manage_clients(request):
    context={
        "page_title":"Manage Clients"
    }
    return render(request,'megacellcnc/manage-clients.html',context)

def blog_1(request):
    context={
        "page_title":"Blog 1"
    }
    return render(request,'megacellcnc/blog-1.html',context)

def svg_icon(request):
    context={
        "page_title":"SVG Icons"
    }
    return render(request,'megacellcnc/svg-icon.html',context)

def auto_write(request):
    context={
        "page_title":"Auto Write"
    }
    return render(request,'megacellcnc/aikit/auto-write.html',context)

def chatbot(request):
    context={
        "page_title":"Chat Bot"
    }
    return render(request,'megacellcnc/aikit/chatbot.html',context)

def fine_tune_models(request):
    context={
        "page_title":"Fine Tune Models"
    }
    return render(request,'megacellcnc/aikit/fine-tune-models.html',context)

def imports(request):
    context={
        "page_title":"Import"
    }
    return render(request,'megacellcnc/aikit/import.html',context)

def prompt(request):
    context={
        "page_title":"Prompt"
    }
    return render(request,'megacellcnc/aikit/prompt.html',context)

def repurpose(request):
    context={
        "page_title":"Repurpose"
    }
    return render(request,'megacellcnc/aikit/repurpose.html',context)

def rss(request):
    context={
        "page_title":"RSS"
    }
    return render(request,'megacellcnc/aikit/rss.html',context)

def scheduled(request):
    context={
        "page_title":"Scheduled"
    }
    return render(request,'megacellcnc/aikit/scheduled.html',context)

def setting(request):
    context={
        "page_title":"Setting"
    }
    return render(request,'megacellcnc/aikit/setting.html',context)

def chat(request):
    context={
        "page_title":"Chat"
    }
    return render(request,'megacellcnc/apps/chat.html',context)

def user(request):
    context={
        "page_title":"User"
    }
    return render(request,'megacellcnc/apps/users/user.html',context)

def user_roles(request):
    context={
        "page_title":"Roles Listing"
    }
    return render(request,'megacellcnc/apps/users/user-roles.html',context)

def app_profile_1(request):
    context={
        "page_title":"App Profile 1"
    }
    return render(request,'megacellcnc/apps/users/app-profile-1.html',context)

def app_profile_2(request):
    context={
        "page_title":"Profile 2"
    }
    return render(request,'megacellcnc/apps/users/app-profile-2.html',context)

def edit_profile(request):
    context={
        "page_title":"Edit Profile"
    }
    return render(request,'megacellcnc/apps/users/edit-profile.html',context)

def post_details(request):
    context={
        "page_title":"Post Details"
    }
    return render(request,'megacellcnc/apps/users/post-details.html',context)

def customer(request):
    context={
        "page_title":"Customer"
    }
    return render(request,'megacellcnc/apps/customer/customer.html',context)

def customer_profile(request):
    context={
        "page_title":"Customer Profile"
    }
    return render(request,'megacellcnc/apps/customer/customer-profile.html',context)

def contacts(request):
    context={
        "page_title":"Contacts"
    }
    return render(request,'megacellcnc/apps/contacts.html',context)


def email_compose(request):
    context={
        "page_title":"Compose"
    }
    return render(request,'megacellcnc/apps/email/email-compose.html',context)


def email_inbox(request):
    context={
        "page_title":"Inbox"
    }
    return render(request,'megacellcnc/apps/email/email-inbox.html',context)


def email_read(request):
    context={
        "page_title":"Read"
    }
    return render(request,'megacellcnc/apps/email/email-read.html',context)


def app_calender(request):
    context={
        "page_title":"Calendar"
    }
    return render(request,'megacellcnc/apps/app-calender.html',context)


def ecom_product_grid(request):
    context={
        "page_title":"Product Grid"
    }
    return render(request,'megacellcnc/apps/shop/ecom-product-grid.html',context)


def ecom_product_list(request):
    context={
        "page_title":"Product List"
    }
    return render(request,'megacellcnc/apps/shop/ecom-product-list.html',context)


def ecom_product_detail(request):
    context={
        "page_title":"Product Detail"
    }
    return render(request,'megacellcnc/apps/shop/ecom-product-detail.html',context)


def ecom_product_order(request):
    context={
        "page_title":"Product Order"
    }
    return render(request,'megacellcnc/apps/shop/ecom-product-order.html',context)


def ecom_checkout(request):
    context={
        "page_title":"Checkout"
    }
    return render(request,'megacellcnc/apps/shop/ecom-checkout.html',context)


def ecom_invoice(request):
    context={
        "page_title":"Invoice"
    }
    return render(request,'megacellcnc/apps/shop/ecom-invoice.html',context)


def ecom_customers(request):
    context={
        "page_title":"Customers"
    }
    return render(request,'megacellcnc/apps/shop/ecom-customers.html',context)


def content(request):
    context={
        "page_title":"Content"
    }
    return render(request,'megacellcnc/cms/content.html',context)


def add_content(request):
    context={
        "page_title":"Add Content"
    }
    return render(request,'megacellcnc/cms/add-content.html',context)


def menu(request):
    context={
        "page_title":"Menu"
    }
    return render(request,'megacellcnc/cms/menu.html',context)


def email_template(request):
    context={
        "page_title":"Email Template"
    }
    return render(request,'megacellcnc/cms/email-template.html',context)


def add_email(request):
    context={
        "page_title":"Add Email"
    }
    return render(request,'megacellcnc/cms/add-email.html',context)


def blog(request):
    context={
        "page_title":"Blog"
    }
    return render(request,'megacellcnc/cms/blog.html',context)


def add_blog(request):
    context={
        "page_title":"Add Blog"
    }
    return render(request,'megacellcnc/cms/add-blog.html',context)


def blog_category(request):
    context={
        "page_title":"Blog Category"
    }
    return render(request,'megacellcnc/cms/blog-category.html',context)


def chart_flot(request):
    context={
        "page_title":"Chart Flot"
    }
    return render(request,'megacellcnc/charts/chart-flot.html',context)


def chart_morris(request):
    context={
        "page_title":"Chart Morris"
    }
    return render(request,'megacellcnc/charts/chart-morris.html',context)


def chart_chartjs(request):
    context={
        "page_title":"Chart Chartjs"
    }
    return render(request,'megacellcnc/charts/chart-chartjs.html',context)


def chart_chartist(request):
    context={
        "page_title":"Chart Chartist"
    }
    return render(request,'megacellcnc/charts/chart-chartist.html',context)


def chart_sparkline(request):
    context={
        "page_title":"Chart Sparkline"
    }
    return render(request,'megacellcnc/charts/chart-sparkline.html',context)


def chart_peity(request):
    context={
        "page_title":"Chart Peity"
    }
    return render(request,'megacellcnc/charts/chart-peity.html',context)



def ui_accordion(request):
    context={
        "page_title":"Accordion"
    }
    return render(request,'megacellcnc/bootstrap/ui-accordion.html',context)


def ui_alert(request):
    context={
        "page_title":"Alert"
    }
    return render(request,'megacellcnc/bootstrap/ui-alert.html',context)


def ui_badge(request):
    context={
        "page_title":"Badge"
    }
    return render(request,'megacellcnc/bootstrap/ui-badge.html',context)


def ui_button(request):
    context={
        "page_title":"Button"
    }
    return render(request,'megacellcnc/bootstrap/ui-button.html',context)


def ui_modal(request):
    context={
        "page_title":"Modal"
    }
    return render(request,'megacellcnc/bootstrap/ui-modal.html',context)


def ui_button_group(request):
    context={
        "page_title":"Button Group"
    }
    return render(request,'megacellcnc/bootstrap/ui-button-group.html',context)


def ui_list_group(request):
    context={
        "page_title":"List Group"
    }
    return render(request,'megacellcnc/bootstrap/ui-list-group.html',context)


def ui_media_object(request):
    context={
        "page_title":"Media Object"
    }
    return render(request,'megacellcnc/bootstrap/ui-media-object.html',context)


def ui_card(request):
    context={
        "page_title":"Card"
    }
    return render(request,'megacellcnc/bootstrap/ui-card.html',context)


def ui_carousel(request):
    context={
        "page_title":"Carousel"
    }
    return render(request,'megacellcnc/bootstrap/ui-carousel.html',context)


def ui_dropdown(request):
    context={
        "page_title":"Dropdown"
    }
    return render(request,'megacellcnc/bootstrap/ui-dropdown.html',context)


def ui_popover(request):
    context={
        "page_title":"Popover"
    }
    return render(request,'megacellcnc/bootstrap/ui-popover.html',context)


def ui_progressbar(request):
    context={
        "page_title":"Progressbar"
    }
    return render(request,'megacellcnc/bootstrap/ui-progressbar.html',context)


def ui_tab(request):
    context={
        "page_title":"Tab"
    }
    return render(request,'megacellcnc/bootstrap/ui-tab.html',context)


def ui_typography(request):
    context={
        "page_title":"Typography"
    }
    return render(request,'megacellcnc/bootstrap/ui-typography.html',context)


def ui_pagination(request):
    context={
        "page_title":"Pagination"
    }
    return render(request,'megacellcnc/bootstrap/ui-pagination.html',context)


def ui_grid(request):
    context={
        "page_title":"Grid"
    }
    return render(request,'megacellcnc/bootstrap/ui-grid.html',context)




def uc_select2(request):
    context={
        "page_title":"Select"
    }
    return render(request,'megacellcnc/plugins/uc-select2.html',context)


def uc_nestable(request):
    context={
        "page_title":"Nestable"
    }
    return render(request,'megacellcnc/plugins/uc-nestable.html',context)


def uc_noui_slider(request):
    context={
        "page_title":"UI Slider"
    }
    return render(request,'megacellcnc/plugins/uc-noui-slider.html',context)


def uc_sweetalert(request):
    context={
        "page_title":"Sweet Alert"
    }
    return render(request,'megacellcnc/plugins/uc-sweetalert.html',context)


def uc_toastr(request):
    context={
        "page_title":"Toastr"
    }
    return render(request,'megacellcnc/plugins/uc-toastr.html',context)


def map_jqvmap(request):
    context={
        "page_title":"Jqvmap"
    }
    return render(request,'megacellcnc/plugins/map-jqvmap.html',context)


def uc_lightgallery(request):
    context={
        "page_title":"LightGallery"
    }
    return render(request,'megacellcnc/plugins/uc-lightgallery.html',context)


def widget_basic(request):
    context={
        "page_title":"Widget"
    }
    return render(request,'megacellcnc/widget-basic.html',context)


def form_element(request):
    context={
        "page_title":"Form Element"
    }
    return render(request,'megacellcnc/forms/form-element.html',context)


def form_wizard(request):
    context={
        "page_title":"Form Wizard"
    }
    return render(request,'megacellcnc/forms/form-wizard.html',context)


def form_editor(request):
    context={
        "page_title":"CkEditor"
    }
    return render(request,'megacellcnc/forms/form-editor.html',context)


def form_pickers(request):
    context={
        "page_title":"Pickers"
    }
    return render(request,'megacellcnc/forms/form-pickers.html',context)







def table_bootstrap_basic(request):
    context={
        "page_title":"Table Bootstrap"
    }
    return render(request,'megacellcnc/table/table-bootstrap-basic.html',context)


def table_datatable_basic(request):
    context={
        "page_title":"Table Datatable"
    }
    return render(request,'megacellcnc/table/table-datatable-basic.html',context)






def page_register(request):
    return render(request,'megacellcnc/pages/page-register.html')

def page_login(request):
    return render(request,'megacellcnc/pages/page-login.html')

def page_forgot_password(request):
    return render(request,'megacellcnc/pages/page-forgot-password.html')

def page_lock_screen(request):
    return render(request,'megacellcnc/pages/page-lock-screen.html')

def page_empty(request):
    context={
        "page_title":"Empty Page"
    }
    return render(request,'megacellcnc/pages/page-empty.html',context)

def page_error_400(request):
    return render(request,'400.html')
    
def page_error_403(request):
    return render(request,'403.html')

def page_error_404(request):
    return render(request,'404.html')

def page_error_500(request):
    return render(request,'500.html')

def page_error_503(request):
    return render(request,'503.html')















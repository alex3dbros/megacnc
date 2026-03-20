
$(document).ready(function() {
    $('.table').each(function() {
        $(this).DataTable({
            'dom': 'ZBfrltip',
            buttons: [
                {
                    extend: 'excel',
                    text: '<i class="fa-solid fa-file-excel"></i> Export Report',
                    className: 'btn btn-outline-primary export-btn'
                }
            ],
            searching: false,
            select: false,
            pageLength: 160,
            lengthChange: false,
            language: {
                paginate: {
                    next: '<i class="fa-solid fa-angle-right"></i>',
                    previous: '<i class="fa-solid fa-angle-left"></i>'
                }
            }
        });
    });
});





function round2(value) {
    const n = Number(value);
    if (value == null || Number.isNaN(n)) return '—';
    return n.toFixed(2);
}

function formatDuration(seconds) {
    // Round the seconds to remove any decimals
    seconds = Math.round(seconds);

    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;

    // Pad to 2 digits, HH:MM:SS
    const hours = h.toString().padStart(2, '0');
    const minutes = m.toString().padStart(2, '0');
    const secondsFormatted = s.toString().padStart(2, '0');

    return `${hours}:${minutes}:${secondsFormatted}`;
}


function updateSlots() {
    const deviceInfoElement = document.getElementById('deviceInfo');
    if (!deviceInfoElement) return;
    const projectID = deviceInfoElement.getAttribute('data-project-id');

    fetch(`/projectdetails/${projectID}/update-slots/`)
        .then(response => response.json())
        .then(devices => {
            let notInsertedCount = 0;
            let regularCellsCount = 0;
            let chargedCount = 0;
            let dischargedCount = 0;
            let lowVoltageCellsCount = 0;
            let chargingCellsCount = 0;
            let dischargingCellsCount = 0;
            let storedCellsCount = 0;
            let badCellsCount = 0;

            devices.forEach(device => {
                device.slots.forEach(slot => {
                    const slotIdPrefix = `device_${device.id}_slot_${slot.slot_number}`;
                    const el = (suffix) => document.getElementById(`${slotIdPrefix}_${suffix}`);
                    const set = (suffix, text) => {
                        const node = el(suffix);
                        if (node) node.textContent = text;
                    };

                    set('number', slot.slot_number);
                    set('voltage', round2(slot.voltage));
                    set('current', round2(slot.current));
                    set('esr', round2(slot.esr));
                    set('capacity', round2(slot.capacity));
                    set('charge_capacity', round2(slot.charge_capacity));
                    set('state', slot.state);
                    set('action_running_time', formatDuration(slot.action_running_time));
                    set('completed_cycles', `${slot.completed_cycles} / ${slot.discharge_cycles_set}`);
                    set('temperature', round2(slot.temperature));
                    set('max_volt', round2(slot.max_volt));
                    set('store_volt', round2(slot.store_volt));
                    set('min_volt', round2(slot.min_volt));
                    set('cell_id', slot.active_cell_uuid);

                    const link = document.querySelector(`a[data-slot-id="${slotIdPrefix}"]`);
                    if (link && slot.capacity != null) {
                        link.setAttribute('data-cell-capacity', Number(slot.capacity).toFixed(2));
                    }

                    if (slot.state === 'Not Inserted') notInsertedCount++;
                    if (slot.state === 'Regular Cell') regularCellsCount++;
                    if (slot.state === 'LVC Cell') lowVoltageCellsCount++;
                    if (slot.state === 'Started Charging' || slot.state === 'LVC Charging' || slot.state === 'mCap Started Charging') {
                        chargingCellsCount++;
                    }
                    if (slot.state === 'Started Discharging') dischargingCellsCount++;
                    if (slot.state === 'Stored') storedCellsCount++;
                    if (slot.state === 'Bad Cell') badCellsCount++;
                    if (slot.state === 'Charged') chargedCount++;
                    if (slot.state === 'Discharged') dischargedCount++;
                });
            });

            // Project-wide totals (all devices)
            const setCount = (id, n) => {
                const node = document.getElementById(id);
                if (node) node.textContent = String(n);
            };
            setCount('count-not-inserted', notInsertedCount);
            setCount('count-regular-cells', regularCellsCount);
            setCount('count-low-voltage', lowVoltageCellsCount);
            setCount('count-charging', chargingCellsCount);
            setCount('count-discharging', dischargingCellsCount);
            setCount('count-charged', chargedCount);
            setCount('count-discharged', dischargedCount);
            setCount('count-stored', storedCellsCount);
            setCount('count-bad', badCellsCount);
        })
        .catch(error => console.error('Error updating slots:', error));
}




updateSlots();
// Call updateSlots every 5 seconds
setInterval(updateSlots, 5000);





function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function addActionListeners(buttonIds) {
    buttonIds.forEach(buttonId => {
        document.getElementById(buttonId).addEventListener('click', function() {
            const action = this.id;  // 'this' refers to the button clicked
            sendAction(action);
        });
    });
}

function sendAction(action) {
    // Gather the checked slot IDs and group by device ID
    const checkedBoxes = document.querySelectorAll('input[name="slot_number"]:checked');
    const devices = {}; // Object to hold device IDs as keys and slot numbers as values

    checkedBoxes.forEach(box => {
        const [prefix, deviceId, slotNumber] = box.value.split('_'); // Split the value into parts
        if (!devices[deviceId]) {
            devices[deviceId] = []; // Initialize the array if it doesn't exist
        }

        devices[deviceId].push(slotNumber); // Add the slot number to the device's array
    });

    // Make sure at least one slot is selected
    if (Object.keys(devices).length === 0) {
        toastr.error('Please select slot(s)', "Error");
        return;
    }

    // Setup the AJAX request for each device
    Object.entries(devices).forEach(([deviceId, slots_number]) => {
        fetch(`/slot/action/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ action, deviceId, slots_number }) // Send device ID and slots for this device
        })
        .then(response => response.json())
        .then(data => {
            toastr.success(`${data.message} for device ${deviceId}`, "Success");
        })
        .catch(error => console.error('Error:', error));
    });
}

// Initialize the listeners for your action buttons
addActionListeners(['charge', 'discharge', 'stop', 'macro', 'stop_macro', 'store', 'esr', 'dispose',]);


function saveCell(slotid, device_id, capacity) {

    let parts = slotid.split("_");
    let slot_id = parts[parts.length - 1];

    fetch("/save-cell/", {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ device_id, slot_id, capacity})
    })
    .then(response => response.json())
    .then(data => {
        //location.reload();  // Optionally reload the page to update the device list

        toastr.success(data.message, "Success");

    })
    .catch(error => console.error('Error:', error));

}



document.querySelectorAll('.saveCellBtn').forEach(btn => {
    btn.addEventListener('click', function() {
        const slotId = this.getAttribute('data-slot-id');
        const deviceId = this.getAttribute('data-device-id');
        const capacity = this.getAttribute('data-cell-capacity');

        saveCell(slotId, deviceId, capacity);
    });
});








$(function() {
    $("#checkSlots").click(function() {
        $(".form-check input[type='checkbox']").prop("checked", $(this).prop("checked"));
    });
});


    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
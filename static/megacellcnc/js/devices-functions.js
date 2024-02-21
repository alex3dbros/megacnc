
// Vars

var current_device_id = 0;


$(function() {
    $("#checkDevices").click(function() {
        $(".form-check input[type='checkbox']").prop("checked", $(this).prop("checked"));
    });
});

// Scanning for new devices
document.getElementById('scanDevicesBtn').addEventListener('click', function() {
    const spinner = document.getElementById('spinner');
    const ipFromInput = document.getElementById('ipFrom');
    const ipToInput = document.getElementById('ipTo');
    let isValid = true;



    // Clear previous styles
    ipFromInput.style.borderColor = '';
    ipToInput.style.borderColor = '';

    // Check if 'IP From' field is empty
    if (!ipFromInput.value.trim()) {
        ipFromInput.style.borderColor = 'red'; // Highlight in red
        isValid = false;
    }

    // Check if 'IP To' field is empty
    if (!ipToInput.value.trim()) {
        ipToInput.style.borderColor = 'red'; // Highlight in red
        isValid = false;
    }

    // If both fields are filled, proceed with the fetch request
    if (isValid) {
        // Show the spinner
        spinner.style.display = 'inline-block';

        const formData = new FormData(document.getElementById('ipRangeForm'));
        fetch('/scan-devices/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        })
            .then(response => response.json())
            .then(data => {

                const deviceListContainer = document.getElementById('deviceList');
                deviceListContainer.innerHTML = ''; // Clear previous results

                // Create a table element
                const table = document.createElement('table');
                table.className = 'table'; // Add Bootstrap table class for styling

                // Create table header
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                ['Select', 'Device Name', 'Device IP', 'Slots', 'Device Type'].forEach(text => {
                    const headerCell = document.createElement('th');
                    headerCell.textContent = text;
                    headerRow.appendChild(headerCell);
                });
                thead.appendChild(headerRow);
                table.appendChild(thead);

                // Create table body
                const tbody = document.createElement('tbody');
                tbody.className = 'scrollable-tbody'; // Add a class for styling

                data.devices.forEach((device, index) => {
                    const row = document.createElement('tr');

                    // Checkbox for selection
                    const selectCell = document.createElement('td');
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.name = 'device' + index;
                    checkbox.value = device.id; // Assuming the device object has an 'id' property
                    selectCell.appendChild(checkbox);
                    row.appendChild(selectCell);

                    // Device Name
                    const nameCell = document.createElement('td');
                    nameCell.textContent = device.name; // Adjust according to your device object properties
                    nameCell.classList.add('device-name');
                    row.appendChild(nameCell);

                    // Device IP
                    const ipCell = document.createElement('td');
                    ipCell.textContent = device.ip; // Adjust according to your device object properties
                    ipCell.classList.add('device-ip');
                    ipCell.setAttribute('data-mac', device.mac);
                    row.appendChild(ipCell);

                    // Device Slot Count
                    const slot_count = document.createElement('td');
                    slot_count.textContent = device.slot_count; // Adjust according to your device object properties
                    slot_count.classList.add('slot-count');
                    row.appendChild(slot_count);


                    // Device Type
                    const typeCell = document.createElement('td');
                    typeCell.textContent = device.type; // Adjust according to your device object properties
                    typeCell.classList.add('device-type');
                    row.appendChild(typeCell);

                    tbody.appendChild(row);
                });

                table.appendChild(tbody);
                deviceListContainer.appendChild(table);

                spinner.style.display = 'none';

            })
            .catch(error => {
                console.error('Error:', error);

                // Hide the spinner in case of error as well
                spinner.style.display = 'none';
            });
    }
});

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


//Add device from modal

document.getElementById('add_device').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    const deviceList = document.getElementById('deviceList');
    const selectedDevices = [];
    let isDeviceSelected = false; // Flag to track if any device is selected

    // Iterate over table rows to find selected devices
    deviceList.querySelectorAll('tbody tr').forEach(row => {
        const checkbox = row.querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.checked) {
            isDeviceSelected = true; // Set flag to true if any checkbox is checked
            const deviceName = row.querySelector('.device-name').textContent;
            const deviceIP = row.querySelector('.device-ip').textContent;
            const deviceType = row.querySelector('.device-type').textContent;
            const deviceMAC = row.querySelector('.device-ip').getAttribute('data-mac');
            const slot_count = row.querySelector('.slot-count').textContent;
            // Extract other details similarly
            selectedDevices.push({name: deviceName, ip: deviceIP , dev_type: deviceType, mac: deviceMAC, slot_count: slot_count});
        }
    });

    if (!isDeviceSelected) {
        // If no device is selected, make the table border red
        deviceList.style.border = '2px solid red';
        return; // Stop the form submission or further processing
    } else {
        // If a device is selected, reset the table border (optional)
        deviceList.style.border = '';
    }

    // Populate the hidden input with selected device details
    document.getElementById('devicesDetails').value = JSON.stringify(selectedDevices);

    this.submit();
});


//Delete device
document.getElementById('deleteDevicesBtn').addEventListener('click', function() {
    const checkedBoxes = document.querySelectorAll('input[name="device_ids"]:checked');
    // Debugging: Log the NodeList of checked checkboxes
    console.log(checkedBoxes);

    const deviceIds = Array.from(checkedBoxes).map(box => box.value);

    if (checkedBoxes.length == 0) {
        toastr.error("No Devices Selected", "Error", {
            timeOut: 5000,
            closeButton: !0,
            debug: !1,
            newestOnTop: !0,
            progressBar: !0,
            positionClass: "toast-top-right",
            preventDuplicates: !0,
            onclick: null,
            showDuration: "300",
            hideDuration: "1000",
            extendedTimeOut: "1000",
            showEasing: "swing",
            hideEasing: "linear",
            showMethod: "fadeIn",
            hideMethod: "fadeOut",
            tapToDismiss: !1
        });
        return;
    }

    fetch("/delete-devices/", {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'device_ids': deviceIds })
    })
        .then(response => response.json())
        .then(data => {
            console.log(data);  // Handle success response
            location.reload();  // Optionally reload the page to update the device list
        })
        .catch(error => console.error('Error:', error));
});


// Delete buttons individual

    // Function to show the confirmation modal
function showDeleteConfirmation(deviceId) {
    // Set the deviceId to a data attribute on the confirm button for later use
    document.getElementById('confirmDeleteBtn').setAttribute('data-device-id', deviceId);

    // Show the modal using Bootstrap's modal method
    var deleteConfirmationModal = new bootstrap.Modal(document.getElementById('deleteConfirmationModal'), {
        keyboard: false
    });
    deleteConfirmationModal.show();
}

// Add event listeners to delete buttons
document.querySelectorAll('.deleteDeviceBtn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();  // Prevent the default link behavior
        const deviceId = this.getAttribute('data-device-id');
        showDeleteConfirmation(deviceId);  // Show confirmation modal
    });
});

// Add event listener to the confirmation button in the modal
document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
    const deviceId = this.getAttribute('data-device-id');
    deleteDevice(deviceId);  // Proceed to delete the device
    $('#deleteConfirmationModal').modal('hide');  // Hide the confirmation modal
});

    // Delete device function
function deleteDevice(deviceId) {
    fetch("/delete-devices/", {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'device_ids': [deviceId] })  // Note that we're sending an array with a single ID
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);  // Handle success response
        location.reload();  // Optionally reload the page to update the device list
    })
    .catch(error => console.error('Error:', error));
}


// Device editing

    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })


function editDevice(deviceId) {

    current_device_id = deviceId;

    // Logic to open the modal and populate it with the device data
    console.log("Edit device", deviceId);

    $('#deviceSettingsModal').modal('show');
    // Show the loading spinner and hide the modal content initially
    $('#loadingSpinner').show();
    // Assuming '.modal-content' is your actual content container
    $('#form-mccpro').hide();
    $('#main-form').hide();
    $('.modal-footer').hide();


    var checkbox = document.getElementById('applyToAllSlots');
    var fieldset = document.getElementById('slotFieldset');

    // Event listener for the checkbox
    checkbox.addEventListener('change', function() {
        // If the checkbox is checked, disable the fieldset
        // If the checkbox is unchecked, enable the fieldset
        fieldset.disabled = this.checked;
    });



    // AJAX call to get device data by deviceId
    fetch("/edit-device/", {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'device_id': deviceId })  // Note that we're sending an array with a single ID
    })
    .then(response => response.json())
    .then(data => {
            // Populate modal form fields with device data

            let labelForChargingCurrent = document.querySelector('label[for="chargingCurrent"]');
            let inputChargingCurrent = document.getElementById('chargingCurrent');
            inputChargingCurrent.removeAttribute('readonly');


            if (data["dev_type"] === "MCC") {

                labelForChargingCurrent.setAttribute('title', 'Charging Current in mA (Readonly)');
                inputChargingCurrent.setAttribute('readonly', "");
                // Reinitialize the tooltip
                var bootstrapTooltip = new bootstrap.Tooltip(labelForChargingCurrent);
                document.getElementById('dischargingCurrent').setAttribute('min', '100');
                document.getElementById('dischargingCurrent').setAttribute('max', '1000');
            }

            document.getElementById('deviceName').value = data["device_name"];
            document.getElementById('minVoltage').value = data["discharge_volt"];
            document.getElementById('storeVoltage').value = data["store_volt"];
            document.getElementById('maxVoltage').value = data["max_charge_volt"];
            document.getElementById('chargingCurrent').value = data["charging_current"];
            document.getElementById('dischargingCurrent').value = data["discharge_current"];
            document.getElementById('maxTemp').value = data["max_temp"];
            document.getElementById('dischargeCycles').value = data["discharge_cycles"];
            document.getElementById('chargingTimeout').value = data["charging_timeout"];
            document.getElementById('firmwareInfo').textContent = data["firmware"];

            if (data["dev_type"] === "MCCPro") {

                labelForChargingCurrent.setAttribute('title', 'Charging Current in mA');
                inputChargingCurrent.removeAttribute('readonly');
                // Reinitialize the tooltip
                var bootstrapTooltip = new bootstrap.Tooltip(labelForChargingCurrent);

                document.getElementById('prechargeCurrent').value = data["pre_charge_current"];
                document.getElementById('termChargingCurrent').value = data["term_charging_current"];

                document.getElementById('dischargeResistance').value = data["discharge_resistance"];

                let selectDischargeModeElement = document.getElementById('dischargeMode');
                selectDischargeModeElement.value = data["discharge_mode"];


                document.getElementById('maxLowVoltTime').value = data["max_low_volt_recovery_time"];

                document.getElementById('maxCapacity').value = data["max_capacity"];

                document.getElementById('slotsNumber').textContent = data["slots_count"];

                document.getElementById('cellsToGroup').value = 16;
                document.getElementById('cellsPerGroup').value = 1;

                document.getElementById('applyToSlot').value = 1;

                document.getElementById('dischargingCurrent').setAttribute('min', '100');
                document.getElementById('dischargingCurrent').setAttribute('max', '3000');
            }



            // Parse the JSON string into a JavaScript object
            var chemistries = JSON.parse(data["chems"]);

            // Initialize the chemistryOptions array and chemistryDefaults object
            var chemistryOptions = [];
            var chemistryDefaults = {};

            chemistries.forEach(function(chemistry) {
                var name = chemistry.fields.name.toLowerCase().replace(/\s+/g, '-'); // Convert name to lowercase and replace spaces with hyphens
                chemistryOptions.push({ value: name, text: chemistry.fields.name });

                chemistryDefaults[name] = {
                    minVoltage: chemistry.fields.min_voltage.toString(),
                    maxVoltage: chemistry.fields.max_voltage.toString(),
                    storeVoltage: chemistry.fields.store_Voltage.toString(),
                    chargingCurrent: chemistry.fields.chg_current.toString(),
                    dischargingCurrent: chemistry.fields.discharge_current.toString(),
                    maxTemp: chemistry.fields.max_temp.toString(),
                    dischargeCycles: chemistry.fields.discharge_cycles.toString(),
                    chargingTimeout: chemistry.fields.max_charge_duration.toString(),
                    maxLowVoltTime: chemistry.fields.low_volt_max_time.toString(),
                    prechargeCurrent: chemistry.fields.pre_chg_current.toString(),
                    termChargingCurrent: chemistry.fields.ter_chg_current.toString(),
                    dischargeResistance: chemistry.fields.discharge_resistance.toString(),
                    dischargeMode: chemistry.fields.discharge_mod.toString(),
                    maxCapacity: chemistry.fields.max_capacity.toString()

                };
            });

            // Add custom option manually if needed
            chemistryOptions.push({ value: "device", text: "Device" });
            chemistryDefaults["device"] = { minVoltage: data["discharge_volt"], maxVoltage: data["max_charge_volt"],
                storeVoltage: data["store_volt"], chargingCurrent: data["charging_current"],
                dischargingCurrent: data["discharge_current"], maxTemp: data["max_temp"],
                dischargeCycles: data["discharge_cycles"], chargingTimeout: data["charging_timeout"],
                maxLowVoltTime: data["max_low_volt_recovery_time"], prechargeCurrent: data["pre_charge_current"],
                termChargingCurrent: data["term_charging_current"], dischargeResistance: data["discharge_resistance"],
                dischargeMode: data["discharge_mode"], maxCapacity: data["max_capacity"]};

            // Populate the select element with options
            var selectElement = document.getElementById('deviceChemistry');
            selectElement.innerHTML = '';
            chemistryOptions.forEach(function(option) {
                var opt = document.createElement('option');
                opt.value = option.value;
                opt.textContent = option.text;
                selectElement.appendChild(opt);
            });


            // Set the default selected value if needed
            selectElement.value = "device"; // Change "device" to the actual value you want to set as default


            // Event listener for the select field change
            document.getElementById('deviceChemistry').addEventListener('change', function() {
                var selectedChemistry = this.value; // Get the selected chemistry value

                // Update the min and max voltage fields based on the selected chemistry
                var defaults = chemistryDefaults[selectedChemistry] || chemistryDefaults['device']; // Fallback to custom if no match

                document.getElementById('minVoltage').value = defaults.minVoltage;
                document.getElementById('maxVoltage').value = defaults.maxVoltage;
                document.getElementById('storeVoltage').value = defaults.storeVoltage;
                document.getElementById('chargingCurrent').value = defaults.chargingCurrent;
                document.getElementById('dischargingCurrent').value = defaults.dischargingCurrent;
                document.getElementById('maxTemp').value = defaults.maxTemp;
                document.getElementById('dischargeCycles').value = defaults.dischargeCycles;
                document.getElementById('chargingTimeout').value = defaults.chargingTimeout;

                document.getElementById('prechargeCurrent').value = defaults.prechargeCurrent;
                document.getElementById('termChargingCurrent').value = defaults.termChargingCurrent;
                document.getElementById('dischargeResistance').value = defaults.dischargeResistance;

                let selectDischargeModeElement = document.getElementById('dischargeMode');
                selectDischargeModeElement.value = defaults.dischargeMode;

                document.getElementById('maxLowVoltTime').value = defaults.maxLowVoltTime;
                document.getElementById('maxCapacity').value = defaults.maxCapacity;

            });



            $('#loadingSpinner').hide();
            $('#main-form').show();
            if (data["dev_type"] === "MCCPro") {
                $('#form-mccpro').show();
            }


            $('.modal-footer').show();
            // Show the modal

        })
        .catch(error => console.error('Error fetching device data:', error));


}

// Add event listeners to edit buttons
document.querySelectorAll('.editDeviceBtn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();  // Prevent the default link behavior
        const deviceId = this.getAttribute('data-device-id');
        editDevice(deviceId);
    });
});



function saveDeviceSettings() {
    var formData = new FormData(document.getElementById('deviceSettingsForm'));
    // Add AJAX call to submit formData to your Django backend
    // Handle success and error responses accordingly
    console.log("This is device id saving");
    console.log(current_device_id);
    $('#deviceSettingsModal').modal('hide'); // Close the modal

    let deviceName = document.getElementById('deviceName').value;
    let minVoltage = document.getElementById('minVoltage').value;
    let storeVoltage = document.getElementById('storeVoltage').value;
    let maxVoltage = document.getElementById('maxVoltage').value;
    let chargingCurrent = document.getElementById('chargingCurrent').value;
    let dischargingCurrent = document.getElementById('dischargingCurrent').value;
    let maxTemp = document.getElementById('maxTemp').value;
    let dischargeCycles = document.getElementById('dischargeCycles').value;
    let chargingTimeout = document.getElementById('chargingTimeout').value;

    // MCCPRO values
    let prechargeCurrent = document.getElementById('prechargeCurrent').value;
    let termChargingCurrent = document.getElementById('termChargingCurrent').value;
    let dischargeResistance = document.getElementById('dischargeResistance').value;
    let dischargeMode = document.getElementById('dischargeMode').value;
    let maxLowVoltTime = document.getElementById('maxLowVoltTime').value;
    let maxCapacity = document.getElementById('maxCapacity').value;
    let cellsToGroup = document.getElementById('cellsToGroup').value;
    let cellsPerGroup = document.getElementById('cellsPerGroup').value;
    let applyToSlot = document.getElementById('applyToSlot').value;
    let tempSource = document.getElementById('tempSource').value;
    let applyToAllSlotsCheckbox = document.getElementById('applyToAllSlots');
    let applyToAllSlots = applyToAllSlotsCheckbox.checked;

    fetch("/save-device-settings/", {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'device_id': current_device_id, deviceName, minVoltage, storeVoltage, maxVoltage,
        chargingCurrent, dischargingCurrent, maxTemp, dischargeCycles, chargingTimeout, prechargeCurrent,
            termChargingCurrent, dischargeResistance, dischargeMode, maxLowVoltTime, maxCapacity, cellsToGroup,
            cellsPerGroup, applyToSlot, applyToAllSlots, tempSource})
    })
    .then(response => response.json())
    .then(data => {
        //location.reload();  // Optionally reload the page to update the device list

        toastr.success(data.message, "Success");

    })
    .catch(error => console.error('Error:', error));

}





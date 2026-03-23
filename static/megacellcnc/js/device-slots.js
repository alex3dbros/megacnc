var timeoutIDs = {};

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



$(".export-btn").appendTo(".help-desk.slots-table");

/* slot number -> Chart instance for "All history" tab */
var mccSlotHistoryCharts = {};

function mccTfGet() {
    return window.MegaCNCChartTimeframe ? MegaCNCChartTimeframe.get() : '5m';
}

function mccTfSave(v) {
    if (window.MegaCNCChartTimeframe) MegaCNCChartTimeframe.save(v);
}

function round2(value) {
    return Number(value).toFixed(2);
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
    let notInsertedCount = 0;
    let regularCellsCount = 0;
    let lowVoltageCellsCount = 0;
    let chargingCellsCount = 0;
    let dischargingCellsCount = 0;
    let storedCellsCount = 0;
    let badCellsCount = 0;

    const deviceInfoElement = document.getElementById('deviceInfo');
    const deviceID = deviceInfoElement.getAttribute('data-device-id');
    const initialSlotCount = parseInt(deviceInfoElement.getAttribute('data-slot-count'), 10);


    fetch(`/device/${deviceID}/update-slots/`)  // Adjust the URL based on your project's URL structure
        .then(response => response.json())
        .then(updatedSlots => {
            // Check if the number of updated slots is different from the initial count
            if (updatedSlots.length !== initialSlotCount) {
                // The number of slots has changed, reload the page
                window.location.reload();
            } else {
                // Update individual cells using their unique IDs
                updatedSlots.forEach(slot => {
                    document.getElementById(`slot_${slot.slot_number}_number`).textContent = slot.slot_number;
                    document.getElementById(`slot_${slot.slot_number}_voltage`).textContent = round2(slot.voltage);
                    document.getElementById(`slot_${slot.slot_number}_current`).textContent = round2(slot.current);
                    document.getElementById(`slot_${slot.slot_number}_esr`).textContent = round2(slot.esr);
                    document.getElementById(`slot_${slot.slot_number}_capacity`).textContent = round2(slot.capacity);
                    document.getElementById(`slot_${slot.slot_number}_charge_capacity`).textContent = round2(slot.charge_capacity);
                    document.getElementById(`slot_${slot.slot_number}_state`).textContent = slot.state;
                    document.getElementById(`slot_${slot.slot_number}_action_running_time`).textContent = formatDuration(slot.action_running_time);
                    document.getElementById(`slot_${slot.slot_number}_completed_cycles`).textContent = `${slot.completed_cycles} / ${slot.discharge_cycles_set}`;
                    document.getElementById(`slot_${slot.slot_number}_temperature`).textContent = round2(slot.temperature);
                    document.getElementById(`slot_${slot.slot_number}_max_volt`).textContent = round2(slot.max_volt);
                    document.getElementById(`slot_${slot.slot_number}_store_volt`).textContent = round2(slot.store_volt);
                    document.getElementById(`slot_${slot.slot_number}_min_volt`).textContent = round2(slot.min_volt);
                    document.getElementById(`slot_${slot.slot_number}_cell_id`).textContent = slot.active_cell_uuid;

                    let selector = `a[data-slot-id="${slot.slot_number}"]`;
                    let link = document.querySelector(selector);
                    if (link) {
                        link.setAttribute('data-cell-capacity', slot.capacity.toFixed(2));
                    }

                    // Increment counters based on slot state
                    if (slot.state === "Not Inserted") {
                        notInsertedCount++;
                    }

                    if (slot.state === "Regular Cell") {
                        regularCellsCount++;
                    }

                    if (slot.state === "LVC Cell") {
                        lowVoltageCellsCount++;
                    }

                    if (slot.state === "Started Charging" || slot.state === "LVC Charging") {
                        chargingCellsCount++;
                    }

                    if (slot.state === "Started Discharging") {
                        dischargingCellsCount++;
                    }

                    if (slot.state === "Stored") {
                        storedCellsCount++;
                    }

                    if (slot.state === "Bad Cell") {
                        badCellsCount++;
                    }



                });
                document.getElementById('count-not-inserted').textContent = notInsertedCount;
                document.getElementById('count-regular-cells').textContent = regularCellsCount;
                document.getElementById('count-low-voltage').textContent = lowVoltageCellsCount;
                document.getElementById('count-charging').textContent = chargingCellsCount;
                document.getElementById('count-discharging').textContent = dischargingCellsCount;
                document.getElementById('count-stored').textContent = storedCellsCount;
                document.getElementById('count-bad').textContent = badCellsCount;
                var lr = document.getElementById('mcc-last-refresh');
                if (lr) lr.textContent = new Date().toLocaleTimeString();
            }
        })
        .catch(error => console.error('Error updating slots:', error));
}
updateSlots();
// Call updateSlots every 5 seconds
setInterval(updateSlots, 5000);



function addActionListeners(buttonIds) {
    buttonIds.forEach(buttonId => {
        document.getElementById(buttonId).addEventListener('click', function() {
            const action = this.id;  // 'this' refers to the button clicked
            sendAction(action);
        });
    });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function sendAction(action) {
    // Gather the checked device IDs
    const checkedBoxes = document.querySelectorAll('input[name="slot_number"]:checked');
    const slots_number = Array.from(checkedBoxes).map(box => box.value);
    const deviceInfoElement = document.getElementById('deviceInfo');
    const deviceId = deviceInfoElement.getAttribute('data-device-id');

    // Make sure at least one device is selected
    if (slots_number.length === 0) {
        toastr.error('Please select slot(s)', "Error");
        return;
    }


    if (action === "print") {

        let doubleLabel = parseInt(includedValue($("#doubleLabel")));

        if (doubleLabel === 1) {
            let batch_size = 2;
            console.log("this is double label");
            console.log(slots_number);
            if (slots_number.length > 1) {
                for (let i = 0; i <= slots_number.length - batch_size; i += batch_size) {
                    let batch = slots_number.slice(i, i + batch_size);
                    printLabels(batch, deviceId);
                    await sleep(1000);
                }

                // Check if there's an uneven batch at the end
                if (slots_number.length % batch_size !== 0) {
                    // Get the last slot
                    let lastBatch = slots_number.slice(-1);

                    // Print the last slot
                    printLabels(lastBatch, deviceId);
                }
            }





        } else {
            for (let i = 0; i < slots_number.length; i++) {
                printLabels(slots_number[i], deviceId);
                await sleep(1000);
            }


        }


    }

    else {

        // Setup the AJAX request
        fetch(`/slot/action/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ action, slots_number, deviceId })
        })
            .then(response => response.json().then(data => ({ ok: response.ok, data })))
            .then(({ ok, data }) => {
                if (ok) toastr.success(data.message || 'Done', 'Success');
                else toastr.error(data.error || 'Command failed', 'Error');
            })
            .catch(error => {
                console.error('Error:', error);
                toastr.error('Network or server error', 'Error');
            });

    }





}

// Initialize the listeners for your action buttons
addActionListeners(['charge', 'discharge', 'stop', 'macro','stop_macro', 'store', 'esr', 'dispose', 'print']);




$(function() {
    $("#checkSlots").click(function() {
        $(".form-check input[type='checkbox']").prop("checked", $(this).prop("checked"));
    });
});



function saveCell(slot_id, device_id, capacity) {

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




// Listener for save cell button
document.querySelectorAll('.saveCellBtn').forEach(btn => {
    btn.addEventListener('click', function() {
        const slotId = this.getAttribute('data-slot-id');
        const deviceId = this.getAttribute('data-device-id');
        const capacity = this.getAttribute('data-cell-capacity');

        saveCell(slotId, deviceId, capacity);
    });
});

var slotChart = function(deviceId, slot, timeframe) {
    if (jQuery(`#slot_${slot}_chart`).length > 0) {
        const tf = timeframe != null ? timeframe : mccTfGet();
        const canvas = document.getElementById(`slot_${slot}_chart`);
        const ctx = canvas.getContext('2d');
        const grid = 'rgba(148, 163, 184, 0.12)';
        const tick = '#94a3b8';

        if (mccSlotHistoryCharts[slot]) {
            mccSlotHistoryCharts[slot].destroy();
            delete mccSlotHistoryCharts[slot];
        }

        fetch("/get-history/", {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'device_id': deviceId, 'slot_id': slot, 'timeframe': tf })
        })
        .then(response => response.json())
        .then(data => {
            mccSlotHistoryCharts[slot] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            label: "Voltage (V)",
                            data: data.volts,
                            borderColor: "rgba(251, 191, 36, 0.95)",
                            borderWidth: 2,
                            pointRadius: 0,
                            pointHoverRadius: 3,
                            fill: true,
                            backgroundColor: "rgba(251, 191, 36, 0.14)",
                            lineTension: 0.35,
                            yAxisID: 'y-axis-1'
                        },
                        {
                            label: "Current",
                            data: data.current,
                            borderColor: "rgba(59, 130, 246, 0.95)",
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: true,
                            backgroundColor: "rgba(59, 130, 246, 0.12)",
                            lineTension: 0.35,
                            yAxisID: 'y-axis-2'
                        },
                        {
                            label: "Temp (°C)",
                            data: data.temp,
                            borderColor: "rgba(236, 72, 153, 0.9)",
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: true,
                            backgroundColor: "rgba(236, 72, 153, 0.1)",
                            lineTension: 0.35,
                            yAxisID: 'y-axis-3'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { fontColor: '#e2e8f0', fontSize: 11, boxWidth: 10, padding: 14 }
                    },
                    tooltips: { mode: 'index', intersect: false },
                    scales: {
                        yAxes: [
                            {
                                id: 'y-axis-1',
                                type: 'linear',
                                position: 'left',
                                ticks: { beginAtZero: false, fontColor: tick, padding: 6 },
                                gridLines: { color: grid, zeroLineColor: grid }
                            },
                            {
                                id: 'y-axis-2',
                                type: 'linear',
                                position: 'right',
                                ticks: { beginAtZero: true, fontColor: tick, padding: 6 },
                                gridLines: { display: false }
                            },
                            {
                                id: 'y-axis-3',
                                type: 'linear',
                                position: 'right',
                                ticks: { beginAtZero: true, fontColor: tick, padding: 6 },
                                gridLines: { display: false }
                            }
                        ],
                        xAxes: [{
                            ticks: { fontColor: tick, padding: 4, maxRotation: 45 },
                            gridLines: { color: grid, zeroLineColor: grid }
                        }]
                    }
                }
            });
        });
    }
};

$(document).on('change', '.mcc-history-timeframe[data-mcc-context="slots"]', function () {
    var $t = $(this);
    var tf = $t.val();
    mccTfSave(tf);
    slotChart(parseInt($t.attr('data-device-id'), 10), parseInt($t.attr('data-slot'), 10), tf);
});

var chartInstance;
var mccRealtimeCharts = {};

var realtimeChart = function(deviceId, slot) {
    if (jQuery(`#slot_${slot}_realtimechart`).length > 0) {
        const canvas = document.getElementById(`slot_${slot}_realtimechart`);
        const ctx = canvas.getContext('2d');
        const grid = 'rgba(148, 163, 184, 0.12)';
        const tick = '#94a3b8';

        if (mccRealtimeCharts[slot]) {
            mccRealtimeCharts[slot].destroy();
            delete mccRealtimeCharts[slot];
        }

        fetch("/get-history/", {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'device_id': deviceId, 'slot_id': slot, 'timeframe': 'rt_10s' })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('get-history (realtime):', data.error);
            }
            var volts = data.volts || [];
            var cur = data.current || [];
            var temps = data.temp || [];
            chartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels || [],
                    datasets: [
                        {
                            label: "Voltage (V)",
                            data: volts,
                            borderColor: "rgba(251, 191, 36, 0.95)",
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: true,
                            backgroundColor: "rgba(251, 191, 36, 0.14)",
                            lineTension: 0.35,
                            yAxisID: 'y-axis-1'
                        },
                        {
                            label: "Current",
                            data: cur,
                            borderColor: "rgba(59, 130, 246, 0.95)",
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: true,
                            backgroundColor: "rgba(59, 130, 246, 0.12)",
                            lineTension: 0.35,
                            yAxisID: 'y-axis-2'
                        },
                        {
                            label: "Temp (°C)",
                            data: temps,
                            borderColor: "rgba(236, 72, 153, 0.9)",
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: true,
                            backgroundColor: "rgba(236, 72, 153, 0.1)",
                            lineTension: 0.35,
                            yAxisID: 'y-axis-3'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { fontColor: '#e2e8f0', fontSize: 11, boxWidth: 10, padding: 14 }
                    },
                    tooltips: { mode: 'index', intersect: false },
                    scales: {
                        yAxes: [
                            {
                                id: 'y-axis-1',
                                type: 'linear',
                                position: 'left',
                                ticks: { beginAtZero: false, fontColor: tick, padding: 6 },
                                gridLines: { color: grid, zeroLineColor: grid }
                            },
                            {
                                id: 'y-axis-2',
                                type: 'linear',
                                position: 'right',
                                ticks: { beginAtZero: true, fontColor: tick, padding: 6 },
                                gridLines: { display: false }
                            },
                            {
                                id: 'y-axis-3',
                                type: 'linear',
                                position: 'right',
                                ticks: { beginAtZero: true, fontColor: tick, padding: 6 },
                                gridLines: { display: false }
                            }
                        ],
                        xAxes: [{
                            ticks: { fontColor: tick, padding: 4, maxRotation: 45 },
                            gridLines: { color: grid, zeroLineColor: grid }
                        }]
                    }
                }
            });
            mccRealtimeCharts[slot] = chartInstance;
            requestAnimationFrame(function () {
                if (mccRealtimeCharts[slot]) {
                    mccRealtimeCharts[slot].resize();
                }
            });
        })
        .catch(function (err) {
            console.error('realtimeChart fetch:', err);
        });
    }
}


function updateRealtimeChart(chart, deviceId, slot) {
    fetch("/get-history/", {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'device_id': deviceId, 'slot_id': slot, 'timeframe': 'rt_10s' })
    })
    .then(response => response.json())
    .then(data => {
        if (!chart || data.error) return;
        chart.data.labels = data.labels || [];
        chart.data.datasets[0].data = data.volts || [];
        chart.data.datasets[1].data = data.current || [];
        chart.data.datasets[2].data = data.temp || [];
        chart.update();
        requestAnimationFrame(function () {
            chart.resize();
        });
    })
    .catch(function (err) {
        console.error('updateRealtimeChart:', err);
    });
}



var flotRealtime1 = function(deviceId, slot) {
    let realtimecontainerId = `#slot_${slot}_realtimechart`;
    var plot4;

    // Function to fetch data from the server
    function fetchData() {
        return fetch(`/get-realtime/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'device_id': deviceId, 'slot_id': slot })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Transform the data if necessary to fit the Flot data format
            return data.chartData; // Example transformation
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            return []; // Return an empty array in case of error to avoid breaking the chart
        });
    }

    // Set up the control widget
    var updateInterval = 1000;

        var data = [], totalPoints = 50;

    function getRandomData() {
        if (data.length > 0)
            data = data.slice(1);
        while (data.length < totalPoints) {
            var prev = data.length > 0 ? data[data.length - 1] : 50,
                y = prev + Math.random() * 10 - 5;
            if (y < 0) {
                y = 0;
            } else if (y > 100) {
                y = 100;
            }
            data.push(y);
        }
        var res = [];
        for (var i = 0; i < data.length; ++i) {
            res.push([i, data[i]])
        }
        return res;
    }


function update_plot4() {
    fetchData().then(newData => {
        if (!Array.isArray(newData)) {
            console.error('Fetched data is not an array:', newData);
            throw new TypeError('Fetched data is not an array');
        }

        if (plot4) {
            console.log([newData]);
            console.log(timeoutIDs);
            plot4.setData([newData]);
            plot4.draw();
        } else {
            // Initialize the plot if it doesn't exist yet
            plot4 = $.plot(realtimecontainerId, [newData], {
                colors: ['#0d99ff'],
                series: {
                    lines: {
                        show: true,
                        lineWidth: 1
                    },
                    shadowSize: 0  // Drawing is faster without shadows
                },
                grid: {
                    borderColor: 'transparent',
                    borderWidth: 1,
                    labelMargin: 5
                },
                xaxis: {
                    mode: 'time',
                    color: 'transparent',
                    font: {
                        size: 10,
                        color: '#858282'
                    }
                },
                yaxis: {
                    min: 2,
                    // max value might need to be dynamic based on your data
                    max: 4.4,  // Adjust according to your data range
                    color: 'transparent',
                    font: {
                        size: 10,
                        color: '#858282'
                    }
                }
            });
        }
        timeoutIDs[slot] = setTimeout(() => update_plot4(slot), updateInterval);
        //setTimeout(update_plot4, updateInterval);
    });
}


    update_plot4(); // Start the update loop
}



function initializeChart(deviceId, slot) {

    var $container = $(`#slot_${slot}_chart`);
    $container.empty();
    $container.data('chart-initialized', false)

    if ($container.is(':visible') && !$container.data('chart-initialized')) {
        slotChart(deviceId, slot, mccTfGet());
        $container.data('chart-initialized', true);
    }

}

var updateIntervalID;
function setupTabEvents(slot, deviceId) {
    // Remove any existing 'shown.bs.tab' event handlers to prevent duplication
    $('a[data-bs-toggle="tab"]').off('shown.bs.tab').on('shown.bs.tab', function (e) {
        let target = $(e.target).attr("href");
        let $realtimecontainer = $(`#slot_${slot}_realtimechart`);
        $realtimecontainer.data('chart-initialized', false);
        console.log(target);

        let $container = $(`#slot_${slot}_chart`);
        $container.data('chart-initialized', false);

        // Assuming $container is defined and accessible in this scope
        if (target === `#navpills-1_slot${slot}` && !$container.data('chart-initialized')) {
            if (mccRealtimeCharts[slot]) {
                mccRealtimeCharts[slot].destroy();
                delete mccRealtimeCharts[slot];
            }
            clearInterval(updateIntervalID);
            slotChart(deviceId, slot, mccTfGet());
            var $sel = $(`.mcc-history-timeframe[data-mcc-context="slots"][data-slot="${slot}"]`);
            if ($sel.length) $sel.val(mccTfGet());
            $container.data('chart-initialized', true);
        }

        if (target === `#navpills-2_slot${slot}` && !$realtimecontainer.data('chart-initialized')) {
            //flotRealtime1(deviceId, slot);
            realtimeChart(deviceId, slot);
            clearInterval(updateIntervalID);
            updateIntervalID = setInterval(function() {
                updateRealtimeChart(chartInstance, deviceId, slot);
            }, 10000); // Update every 10000 milliseconds (10 seconds)


            $realtimecontainer.data('chart-initialized', true);
        }
    });
}




// Delegated + explicit data-* reads (jQuery .data('slot-number') is unreliable vs data-slot-number)
$(document).on('click', '.expandBtn', function (e) {
    e.preventDefault();

    var $btn = $(this);
    var $allAccordions = $('.accordion-content');

    var $triggerRow = $btn.closest('tr');
    var $nextRow = $triggerRow.next('.accordion-content');
    var slotNumber = parseInt($btn.attr('data-slot-number'), 10);
    var deviceId = parseInt($btn.attr('data-device-id'), 10);
    if (isNaN(slotNumber) || isNaN(deviceId)) {
        console.error('expandBtn: missing data-slot-number or data-device-id', $btn[0]);
        return;
    }
    clearInterval(updateIntervalID);
    // Hide and remove all other accordion contents except for the current one
    $allAccordions.not($nextRow).hide().remove();

    if ($nextRow.length) {
        // Accordion row exists, toggle its visibility
        $nextRow.toggle();

        if (!$nextRow.is(':visible')) {
            clearInterval(updateIntervalID);
            $nextRow.remove();

        }


    } else {
        // Accordion row does not exist, create and inject it with dynamic slot number in the ID
        var colspan = $triggerRow.children('td').length; // Number of columns in the row
        var accordionRow = `
            <tr class="accordion-content" data-slot-number="${slotNumber}">
                <td colspan="${colspan}">
                    <div class="mcc-chart-panel">
                        <h4 class="card-title mb-3">Slot ${slotNumber} — Voltage, current &amp; temperature</h4>
                        <div class="d-flex flex-wrap align-items-center gap-2 mb-3 mcc-history-toolbar">
                            <label class="small text-muted mb-0">History resolution</label>
                            <select class="form-select form-select-sm mcc-history-timeframe" style="max-width: 15rem" data-mcc-context="slots" data-device-id="${deviceId}" data-slot="${slotNumber}" id="mcc_hist_tf_slot_${slotNumber}">
                                ${window.MegaCNCChartTimeframe ? MegaCNCChartTimeframe.optionTags() : '<option value="5m" selected>5 min (default, fast)</option><option value="1m">1 min</option><option value="30s">30 sec</option><option value="10s">10 sec (dense)</option>'}
                            </select>
                        </div>
                        <ul class="nav nav-pills mb-3 light" role="tablist">
                            <li class="nav-item" role="presentation">
                                <a href="#navpills-1_slot${slotNumber}" class="nav-link active" data-bs-toggle="tab" role="tab" aria-selected="true">All history</a>
                            </li>
                            <li class="nav-item" role="presentation">
                                <a href="#navpills-2_slot${slotNumber}" class="nav-link" data-bs-toggle="tab" role="tab" aria-selected="false">Realtime</a>
                            </li>
                        </ul>
                        <div class="tab-content">
                            <div id="navpills-1_slot${slotNumber}" class="tab-pane fade show active" role="tabpanel">
                                <div class="mcc-chart-canvas-wrap">
                                    <canvas id="slot_${slotNumber}_chart"></canvas>
                                </div>
                            </div>
                            <div id="navpills-2_slot${slotNumber}" class="tab-pane fade" role="tabpanel">
                                <div class="mcc-chart-canvas-wrap">
                                    <canvas id="slot_${slotNumber}_realtimechart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        `;

        // Inject the new row after the trigger row and make sure it's visible
        $(accordionRow).insertAfter($triggerRow).show();
        setupTabEvents(slotNumber, deviceId);
    }

    initializeChart(deviceId, slotNumber);
});

jQuery(function () {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        tooltipTriggerList.forEach(function (tooltipTriggerEl) {
            try {
                new bootstrap.Tooltip(tooltipTriggerEl);
            } catch (err) {
                console.warn('Tooltip init:', err);
            }
        });
    }
});
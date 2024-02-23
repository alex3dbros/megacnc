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

function sendAction(action) {
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
            .then(response => response.json())
            .then(data => {

                toastr.success(data.message, "Success");


            })
            .catch(error => console.error('Error:', error));

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

var slotChart = function(deviceId, slot) {
    // Dual line chart
    if (jQuery(`#slot_${slot}_chart`).length > 0) {
        const lineChart_3 = document.getElementById(`slot_${slot}_chart`).getContext('2d');

        // Generate gradients
        const lineChart_3gradientStroke1 = lineChart_3.createLinearGradient(500, 0, 100, 0);
        lineChart_3gradientStroke1.addColorStop(0, "rgb(175,165,1)");
        lineChart_3gradientStroke1.addColorStop(1, "rgb(175,165,1)");

        const lineChart_3gradientStroke2 = lineChart_3.createLinearGradient(500, 0, 100, 0);
        lineChart_3gradientStroke2.addColorStop(0, "rgba(255, 92, 0, 1)");
        lineChart_3gradientStroke2.addColorStop(1, "rgba(255, 92, 0, 1)");

        const lineChart_3gradientStroke3 = lineChart_3.createLinearGradient(500, 0, 100, 0);
        lineChart_3gradientStroke3.addColorStop(0, "rgb(0,255,224)");
        lineChart_3gradientStroke3.addColorStop(1, "rgb(0,255,224)");


        // Save the original draw function
        var originalLineDraw = Chart.controllers.line.prototype.draw;

        // Extend the line chart controller to include custom drawing behavior
        Chart.controllers.line = Chart.controllers.line.extend({
            draw: function() {
                originalLineDraw.apply(this, arguments); // Call the original draw function

                let ctx = this.chart.ctx;
                let _stroke = ctx.stroke;
                ctx.stroke = function() {
                    ctx.save();
                    ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
                    ctx.shadowBlur = 10;
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 4;
                    _stroke.apply(this, arguments);
                    ctx.restore();
                };
            }
        });

                // AJAX call to get device data by deviceId
        fetch("/get-history/", {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'device_id': deviceId, 'slot_id': slot, 'timeframe': "5m" })
        })
        .then(response => response.json())
        .then(data => {
            console.log(data)
            new Chart(lineChart_3, {
                type: 'line',
                data: {
                    defaultFontFamily: 'Poppins',
                    labels: data.labels,
                    datasets: [
                        {
                            label: "V",
                            data: data.volts,
                            borderColor: lineChart_3gradientStroke1,
                            borderWidth: "2",
                            backgroundColor: 'transparent',
                            pointBackgroundColor: 'rgba(0,227,6,0.5)',
                            yAxisID: 'y-axis-1'
                        },
                        {
                            label: "C",
                            data: data.current,
                            borderColor: lineChart_3gradientStroke2,
                            borderWidth: "2",
                            backgroundColor: 'transparent',
                            pointBackgroundColor: 'rgba(255, 92, 0, 1)',
                            yAxisID: 'y-axis-2'
                        },

                        {
                            label: "Temp",
                            data: data.temp,
                            borderColor: lineChart_3gradientStroke3,
                            borderWidth: "2",
                            backgroundColor: 'transparent',
                            pointBackgroundColor: 'rgb(15,196,252)',
                            yAxisID: 'y-axis-3'
                        }

                    ]
                },
                options: {
                    legend: {
                        display: true, // This will show the legend
                        position: 'top', // Position of the legend. Possible values: 'top', 'left', 'bottom', 'right'
                        labels: {
                            fontColor: '#ffffff', // Color of the text in the legend
                            fontSize: 12, // Size of the text in the legend
                            // You can add more styling options as needed
                        }
                    },
                    scales: {
                        yAxes: [
                            {
                                id: 'y-axis-1',
                                type: 'linear',
                                position: 'left',
                                ticks: {
                                    beginAtZero: true, // Starts the scale at 0
                                    fontColor: '#ffffff',
                                    // No need to set max and min; Chart.js will adjust automatically
                                },
                                gridLines: {
                                    color: "rgba(255, 255, 255, 0.1)"
                                }
                            },
                            {
                                id: 'y-axis-2',
                                type: 'linear',
                                position: 'right',
                                ticks: {
                                    beginAtZero: true, // Starts the scale at 0
                                    fontColor: '#ffffff',
                                    // No need to set max and min; Chart.js will adjust automatically
                                },
                                gridLines: {
                                    color: "rgba(255, 255, 255, 0.1)",
                                    drawOnChartArea: false, // Only want the grid lines for one axis to show up
                                }
                            },

                            {
                                id: 'y-axis-3',
                                type: 'linear',
                                position: 'right',
                                ticks: {
                                    beginAtZero: true, // Starts the scale at 0
                                    fontColor: '#ffffff',
                                    // No need to set max and min; Chart.js will adjust automatically
                                },
                                gridLines: {
                                    color: "rgba(255, 255, 255, 0.1)",
                                    drawOnChartArea: false, // Only want the grid lines for one axis to show up
                                }
                            }


                        ],
                        xAxes: [{
                            ticks: {
                                padding: 5,
                                fontColor: '#ffffff',
                            },
                            gridLines: {
                                color: "rgba(255, 255, 255, 0.1)"
                            }
                        }]
                    }
                }
            });
        });
    }
}

var chartInstance;

var realtimeChart = function(deviceId, slot) {
    // Dual line chart
    if (jQuery(`#slot_${slot}_chart`).length > 0) {
        const lineChart_3 = document.getElementById(`slot_${slot}_realtimechart`).getContext('2d');

        // Generate gradients
        const lineChart_3gradientStroke1 = lineChart_3.createLinearGradient(500, 0, 100, 0);
        lineChart_3gradientStroke1.addColorStop(0, "rgb(175,165,1)");
        lineChart_3gradientStroke1.addColorStop(1, "rgb(175,165,1)");

        const lineChart_3gradientStroke2 = lineChart_3.createLinearGradient(500, 0, 100, 0);
        lineChart_3gradientStroke2.addColorStop(0, "rgba(255, 92, 0, 1)");
        lineChart_3gradientStroke2.addColorStop(1, "rgba(255, 92, 0, 1)");

        const lineChart_3gradientStroke3 = lineChart_3.createLinearGradient(500, 0, 100, 0);
        lineChart_3gradientStroke3.addColorStop(0, "rgb(0,255,224)");
        lineChart_3gradientStroke3.addColorStop(1, "rgb(0,255,224)");


        // Save the original draw function
        var originalLineDraw = Chart.controllers.line.prototype.draw;

        // Extend the line chart controller to include custom drawing behavior
        Chart.controllers.line = Chart.controllers.line.extend({
            draw: function() {
                originalLineDraw.apply(this, arguments); // Call the original draw function

                let ctx = this.chart.ctx;
                let _stroke = ctx.stroke;
                ctx.stroke = function() {
                    ctx.save();
                    ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
                    ctx.shadowBlur = 10;
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 4;
                    _stroke.apply(this, arguments);
                    ctx.restore();
                };
            }
        });

                // AJAX call to get device data by deviceId
        fetch("/get-history/", {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'device_id': deviceId, 'slot_id': slot, 'timeframe': "10s"})
        })
        .then(response => response.json())
        .then(data => {
            console.log(data)
            chartInstance = new Chart(lineChart_3, {
                type: 'line',
                data: {
                    defaultFontFamily: 'Poppins',
                    labels: data.labels,
                    datasets: [
                        {
                            label: "V",
                            data: data.volts,
                            borderColor: lineChart_3gradientStroke1,
                            borderWidth: "2",
                            backgroundColor: 'transparent',
                            pointBackgroundColor: 'rgba(0,227,6,0.5)',
                            yAxisID: 'y-axis-1'
                        },
                        {
                            label: "C",
                            data: data.current,
                            borderColor: lineChart_3gradientStroke2,
                            borderWidth: "2",
                            backgroundColor: 'transparent',
                            pointBackgroundColor: 'rgba(255, 92, 0, 1)',
                            yAxisID: 'y-axis-2'
                        },

                        {
                            label: "Temp",
                            data: data.temp,
                            borderColor: lineChart_3gradientStroke3,
                            borderWidth: "2",
                            backgroundColor: 'transparent',
                            pointBackgroundColor: 'rgb(15,196,252)',
                            yAxisID: 'y-axis-3'
                        }

                    ]
                },
                options: {
                    legend: {
                        display: true, // This will show the legend
                        position: 'top', // Position of the legend. Possible values: 'top', 'left', 'bottom', 'right'
                        labels: {
                            fontColor: '#ffffff', // Color of the text in the legend
                            fontSize: 12, // Size of the text in the legend
                            // You can add more styling options as needed
                        }
                    },
                    scales: {
                        yAxes: [
                            {
                                id: 'y-axis-1',
                                type: 'linear',
                                position: 'left',
                                ticks: {
                                    beginAtZero: false, // Starts the scale at 0
                                    fontColor: '#ffffff',
                                    // No need to set max and min; Chart.js will adjust automatically
                                },
                                gridLines: {
                                    color: "rgba(255, 255, 255, 0.1)"
                                }
                            },
                            {
                                id: 'y-axis-2',
                                type: 'linear',
                                position: 'right',
                                ticks: {
                                    beginAtZero: true, // Starts the scale at 0
                                    fontColor: '#ffffff',
                                    // No need to set max and min; Chart.js will adjust automatically
                                },
                                gridLines: {
                                    color: "rgba(255, 255, 255, 0.1)",
                                    drawOnChartArea: false, // Only want the grid lines for one axis to show up
                                }
                            },

                            {
                                id: 'y-axis-3',
                                type: 'linear',
                                position: 'right',
                                ticks: {
                                    beginAtZero: true, // Starts the scale at 0
                                    fontColor: '#ffffff',
                                    // No need to set max and min; Chart.js will adjust automatically
                                },
                                gridLines: {
                                    color: "rgba(255, 255, 255, 0.1)",
                                    drawOnChartArea: false, // Only want the grid lines for one axis to show up
                                }
                            }


                        ],
                        xAxes: [{
                            ticks: {
                                padding: 5,
                                fontColor: '#ffffff',
                            },
                            gridLines: {
                                color: "rgba(255, 255, 255, 0.1)"
                            }
                        }]
                    }
                }
            });
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
        body: JSON.stringify({ 'device_id': deviceId, 'slot_id': slot, 'timeframe': "10s"})
    })
    .then(response => response.json())
    .then(data => {
        chart.data.labels = data.labels;
        chart.data.datasets[0].data = data.volts; // Update voltage data
        chart.data.datasets[1].data = data.current; // Update current data
        chart.data.datasets[2].data = data.temp; // Update capacity data

        chart.update();
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
        slotChart(deviceId, slot);
        $container.data('chart-initialized', true);
    }

}

var updateIntervalID;
function setupTabEvents(slot, deviceId) {
    // Remove any existing 'shown.bs.tab' event handlers to prevent duplication
    $('a[data-bs-toggle="tab"]').off('shown.bs.tab').on('shown.bs.tab', function (e) {
        let target = $(e.target).attr("href");
        let $realtimecontainer = $(`#slot_${slot}_realtimechart`);
        $realtimecontainer.empty();
        $realtimecontainer.data('chart-initialized', false)
        console.log(target);

        let $container = $(`#slot_${slot}_chart`);
        $container.empty();
        $container.data('chart-initialized', false)

        // Assuming $container is defined and accessible in this scope
        if (target === `#navpills-1_slot${slot}` && !$container.data('chart-initialized')) {
            slotChart(deviceId, slot);
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




$('.expandBtn').click(function() {


    var $allAccordions = $('.accordion-content');


    var $triggerRow = $(this).closest('tr'); // The row where the button was clicked
    var $nextRow = $triggerRow.next('.accordion-content'); // The next row, which might be the accordion content
    var slotNumber = $(this).data('slot-number'); // Retrieve the slot number from the button's data attribute
    let deviceId = $(this).data('device-id');
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
                    <div class="col-xl-6 col-lg-6">
                        <div class="card">
                            <div class="card-header">
                                <h4 class="card-title">Slot ${slotNumber} Chart</h4>
                            </div>
                            
                            
                            
                            <ul class="nav nav-pills mb-4 light">
                                <li class=" nav-item">
                                    <a href="#navpills-1_slot${slotNumber}" class="nav-link active" data-bs-toggle="tab" aria-expanded="false">All History</a>
                                </li>
                                <li class="nav-item">
                                    <a href="#navpills-2_slot${slotNumber}" class="nav-link" data-bs-toggle="tab" aria-expanded="false">Realtime</a>
                                </li>
                            </ul>
                            <div class="tab-content">
                                <div id="navpills-1_slot${slotNumber}" class="tab-pane active">
                                    <div class="row">
                                        <div class="col-md-12">                             
                                                <canvas id="slot_${slotNumber}_chart"></canvas>
                                        </div>
                                    </div>
                                </div>
                                <div id="navpills-2_slot${slotNumber}" class="tab-pane">
                                    <div class="row">
                                        <div class="col-md-12"> 
                                            <canvas id="slot_${slotNumber}_realtimechart"></canvas>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            
                            
                            

                        </div>
                    </div>
                </td>
            </tr>
        `;

        // Inject the new row after the trigger row and make sure it's visible
        $(accordionRow).insertAfter($triggerRow).show(); // Using .show() here is optional since new content should be visible by default
        // After creating new content, set up the tab events
        var slot = $(this).data('slot-number'); // Retrieve the slot number
        let deviceId = $(this).data('device-id'); // Retrieve the device ID
        setupTabEvents(slot, deviceId);
    }


    initializeChart( deviceId, slotNumber);


});

    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
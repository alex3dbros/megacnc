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

function formatDuration(seconds) {
    const days = Math.floor(seconds / (3600 * 24));
    seconds %= 3600 * 24;
    const hours = Math.floor(seconds / 3600);
    seconds %= 3600;
    const minutes = Math.floor(seconds / 60);
    seconds %= 60;

    // Round the seconds to the nearest whole number
    seconds = Math.round(seconds); // Or use toFixed(0) if you prefer to return a string

    const parts = [];
    if (days > 0) parts.push(days + ' day' + (days > 1 ? 's' : ''));
    if (hours > 0) parts.push(hours + ' hour' + (hours > 1 ? 's' : ''));
    if (minutes > 0) parts.push(minutes + ' minute' + (minutes > 1 ? 's' : ''));
    if (seconds > 0 || parts.length === 0) { // Also show '0 seconds' if it's the only unit
        parts.push(seconds + ' second' + (seconds !== 1 ? 's' : ''));
    }

    return parts.join(', ');
}


function initializeChart(deviceId, cellId) {

    var $container = $(`#cell_${cellId}_chart`);
    $container.empty();
    $container.data('chart-initialized', false)

    if ($container.is(':visible') && !$container.data('chart-initialized')) {
        slotChart(deviceId, cellId);
        $container.data('chart-initialized', true);
    }

}


var slotChart = function(deviceId, cellId) {
    // Dual line chart
    if (jQuery(`#cell_${cellId}_chart`).length > 0) {
        const lineChart_3 = document.getElementById(`cell_${cellId}_chart`).getContext('2d');

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
            body: JSON.stringify({ 'device_id': deviceId, 'cell_id': cellId, 'slot_id': -1, 'timeframe': "5m"})
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




function setupTabEvents(cellId, deviceId) {
    console.log("Tab events 1");
    // Remove any existing 'shown.bs.tab' event handlers to prevent duplication
    $('a[data-bs-toggle="tab"]').off('shown.bs.tab').on('shown.bs.tab', function (e) {
        let target = $(e.target).attr("href");
        console.log("Tab events 2");
        let $container = $(`#cell_${cellId}_chart`);
        $container.empty();
        $container.data('chart-initialized', false)

        // Assuming $container is defined and accessible in this scope
        if (target === `#navpills-1_cell${cellId}` && !$container.data('chart-initialized')) {
            slotChart(deviceId, cellId);
            console.log("I called slotchart");
            $container.data('chart-initialized', true);
        }

    });
}


$('#database-tbl').on('click', '.expandBtn', function() {

    var $allAccordions = $('.accordion-content');


    var $triggerRow = $(this).closest('tr'); // The row where the button was clicked
    var $nextRow = $triggerRow.next('.accordion-content'); // The next row, which might be the accordion content


    var cellID = $(this).data('cell-id');
    var UUID = $(this).data('cell-uuid');
    var deviceIp = $(this).data('device-ip');
    var deviceMac = $(this).data('device-mac');
    var deviceType = $(this).data('device-type');
    var deviceSlot = $(this).data('device-slot');
    var capacity = $(this).data('cell-capacity');
    var esr = $(this).data('cell-esr');
    var testDuration = $(this).data('cell-test-duration');

    var chargeDuration= $(this).data('cell-charge-duration');
    var dischargeDuration = $(this).data('cell-discharge-duration');
    var cycles = $(this).data('cell-cycles');
    var tempBeforeTest = $(this).data('cell-temp-before-test');
    var avgTempCharging = $(this).data('cell-avg-temp-charging');
    var avgTempDischarging = $(this).data('cell-avg-temp-discharging');
    var maxTempCharging = $(this).data('cell-max-temp-charging');
    var maxTempDischarging = $(this).data('cell-max-temp-discharging');
    var minVoltage = $(this).data('cell-min-voltage');
    var maxVoltage = $(this).data('cell-max-voltage');
    var storeVoltage = $(this).data('cell-store-voltage');
    var testingCurrent = $(this).data('cell-testing-current');
    var dischargeMode = $(this).data('cell-dicharge-mode');
    var status = $(this).data('cell-status');

    var insertionDate = $(this).data('cell-insertion-date');


    var removalDate = $(this).data('cell-removal-date');
    var available = $(this).data('cell-available');

    let dischargeModeStr;
    console.log(dischargeMode);
    switch (dischargeMode) {
        case 0:
            dischargeModeStr = "CC";
            break;
        case 1:
            dischargeModeStr = "CV";
            break;
        case 2:
            dischargeModeStr = "CR";
            break;
        default:
            dischargeModeStr = "Unknown"; // Default case if none of the cases match
    }


    const options = {
      year: 'numeric', month: 'long', day: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: false, // Use 24-hour format
      timeZoneName: 'short'
    };



    // Formatting the date depending on the timezone of browser
    var formattedInsDate;
    if (!insertionDate || insertionDate === "None"){
        formattedInsDate = "N.A";
    } else {
        var insDate = new Date(insertionDate);
        formattedInsDate = new Intl.DateTimeFormat('en-US', options).format(insDate);
    }

    var formattedRemDate;
    if (!removalDate || removalDate === "None"){
        formattedRemDate = "N.A";
    } else {
        var remDate = new Date(removalDate);
        formattedRemDate = new Intl.DateTimeFormat('en-US', options).format(remDate);
    }

    // Hide and remove all other accordion contents except for the current one
    $allAccordions.not($nextRow).hide().remove();

    if ($nextRow.length) {
        // Accordion row exists, toggle its visibility
        $nextRow.toggle();

        if (!$nextRow.is(':visible')) {
            $nextRow.remove();

        }


    } else {
        console.log("Creating tab");
        // Accordion row does not exist, create and inject it with dynamic slot number in the ID
        var colspan = $triggerRow.children('td').length; // Number of columns in the row
        var accordionRow = `
            <tr class="accordion-content" data-slot-number="${cellID}">
                <td colspan="${colspan}">
                


<div class="col-auto wid-100">
    <div class="row">
    
    
        <div class="col-xl-3 col-sm-6">
            <div class="card chart-grd same-card">
                <div class="card-body depostit-card p-0 text-left-align">
                    <div class="depostit-card-media d-flex justify-content-between pb-0">
                        <div>
                            <h6>Cell ${cellID} Data - ${UUID}</h6>
                        </div>
                    </div>
                    <div class="cell-details mt-3 px-3">
                        <ul class="list-unstyled">
                            <li><strong>Capacity:</strong> ${capacity} mAh</li>
                            <li><strong>ESR:</strong> ${esr} Ohms</li>
                            <li><strong>Cycles:</strong> ${cycles} </li>
                            <li><strong>Available:</strong> ${available} </li>
                            <li class="spacer"></li>
                            <li><strong>Temp Before Test:</strong> ${tempBeforeTest} Celsius</li>
                            <li><strong>Avg Temp Charging:</strong> ${avgTempCharging} Celsius</li>
                            <li><strong>Avg Temp Discharging:</strong> ${avgTempDischarging} </li>
                            <li><strong>Max Temp Charging:</strong> ${maxTempCharging} </li>
                            <li><strong>Max Temp Discharging:</strong> ${maxTempDischarging} </li>
                            <li><strong>Min Voltage:</strong> ${minVoltage} </li>
                            <li><strong>Store Voltage:</strong> ${storeVoltage} </li>
                            <li><strong>Max Voltage:</strong> ${maxVoltage} </li>
                            <li><strong>Discharge Current:</strong> ${testingCurrent} </li>
                            <li><strong>Discharge Mode:</strong> ${dischargeModeStr} </li>
                            <li class="spacer"></li>
                            <li><strong>Status:</strong> ${status} </li>
                            <li><strong>Insertion Date:</strong> ${formattedInsDate} </li>
                            <li><strong>Removal Date:</strong> ${formattedRemDate} </li>
                            <li><strong>Test Length:</strong> ${formatDuration(testDuration)} </li>
                            <li><strong>Charge Duration:</strong> ${formatDuration(chargeDuration)} </li>
                            <li><strong>Discharge Duration:</strong> ${formatDuration(dischargeDuration)} </li>
                            <li class="spacer"></li>
                            <li><strong>Device IP:</strong> ${deviceIp} </li>
                            <li><strong>Device Mac:</strong> ${deviceMac} </li>
                            <li><strong>Device Type:</strong> ${deviceType}</li>
                            <li><strong>Device Slot #:</strong> ${deviceSlot}</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>


    
        <div class="col-xl-8 col-lg-6">
            <div class="card chart-grd same-card">
                <div class="card-body depostit-card p-0">
                    <div>
                        <div>
                                <div class="card-header">
                                    <h4 class="card-title">Chart</h4>
                                </div>
                                
                                <div class="tab-content">
                                    <div id="navpills-1_cell${cellID}" class="tab-pane active">
                                        <div class="row">
                                            <div class="col-md-12">                             
                                                    <canvas id="cell_${cellID}_chart"></canvas>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                
                             
                        </div>
                    
                    </div>
                    <!--\t\t\t\t\t\t\t\t<div id="NewCustomers"></div>-->
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
        var cellId = $(this).data('cell-id'); // Retrieve the slot number
        let deviceId = $(this).data('device-id'); // Retrieve the device ID
        console.log("before setup datb events");
        setupTabEvents(cellId, -1);


    }

    initializeChart( -1, cellId);

});



//Delete cells
document.getElementById('deleteCellsBtn').addEventListener('click', function() {
    const checkedBoxes = document.querySelectorAll('input[name="cell_ids"]:checked');
    if (checkedBoxes.length === 0) {
        toastr.error("No Cells Selected", "Error");
        return;
    }

    // Convert NodeList to array and map to values
    const cellIds = Array.from(checkedBoxes).map(box => box.value);

    // Show confirmation modal for deletion
    showBulkDeleteConfirmation(cellIds);
});

// Function to display a confirmation modal for bulk deletion
function showBulkDeleteConfirmation(cellIds) {
    // Update modal with the number of cells being deleted
    const modalText = document.getElementById('modalText');
    modalText.textContent = `Are you sure you want to delete ${cellIds.length} cell(s)?`;

    // Set data attribute with cell IDs on confirm button
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    confirmDeleteBtn.setAttribute('data-cell-ids', JSON.stringify(cellIds));

    // Show modal
    var deleteConfirmationModal = new bootstrap.Modal(document.getElementById('deleteConfirmationModal'), {
        keyboard: false
    });
    deleteConfirmationModal.show();
}

// Adjusting existing code to handle bulk delete confirmation
document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
    const cellIds = JSON.parse(this.getAttribute('data-cell-ids'));  // Retrieve array of IDs
    deleteCells(cellIds);
    $('#deleteConfirmationModal').modal('hide');  // Hide modal after confirmation
});

// Function to delete cells
function deleteCells(cellIds) {
    fetch("/delete-cells/", {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'cell_ids': cellIds })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);  // Log response
        location.reload();  // Reload to update UI
    })
    .catch(error => console.error('Error:', error));
}


// Delete buttons individual

    // Function to show the confirmation modal
function showDeleteConfirmation(cellId) {
    // Set the deviceId to a data attribute on the confirm button for later use
    document.getElementById('confirmDeleteBtn').setAttribute('data-cell-id', cellId);

    // Show the modal using Bootstrap's modal method
    var deleteConfirmationModal = new bootstrap.Modal(document.getElementById('deleteConfirmationModal'), {
        keyboard: false
    });
    deleteConfirmationModal.show();
}

// Add event listeners to delete buttons
document.querySelectorAll('.deleteCellBtn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();  // Prevent the default link behavior
        const cellId = this.getAttribute('data-cell-id');

        showDeleteConfirmation(cellId);  // Show confirmation modal
    });
});

// Add event listener to the confirmation button in the modal
document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
    const cellId = this.getAttribute('data-cell-id');
    console.log(cellId);
    deleteCell(cellId);  // Proceed to delete the device
    $('#deleteConfirmationModal').modal('hide');  // Hide the confirmation modal
});

    // Delete device function
function deleteCell(cellId) {
    fetch("/delete-cells/", {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'cell_ids': [cellId] })  // Note that we're sending an array with a single ID
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);  // Handle success response
        location.reload();  // Optionally reload the page to update the cells list
    })
    .catch(error => console.error('Error:', error));
}




async function sendAction(action) {
    // Gather the checked device IDs
    const checkedBoxes = document.querySelectorAll('input[name="cell_ids"]:checked');
    const cell_ids = Array.from(checkedBoxes).map(box => box.value);

    // Make sure at least one cell is selected
    if (cell_ids.length === 0) {
        toastr.error('Please select cell(s)', "Error");
        return;
    }


    if (action === "print") {

        let doubleLabel = parseInt(includedValue($("#doubleLabel")));

        if (doubleLabel === 1) {
            let batch_size = 2;
            console.log("this is double label");
            console.log(cell_ids);
            if (cell_ids.length > 1) {
                for (let i = 0; i <= cell_ids.length - batch_size; i += batch_size) {
                    let batch = cell_ids.slice(i, i + batch_size);
                    printLabels(batch, -1);
                    await sleep(1000);
                }

                // Check if there's an uneven batch at the end
                if (cell_ids.length % batch_size !== 0) {
                    // Get the last slot
                    let lastBatch = cell_ids.slice(-1);

                    // Print the last slot
                    printLabels(lastBatch, -1);
                }
            }





        } else {
            for (let i = 0; i < cell_ids.length; i++) {
                printLabels(cell_ids[i], -1);
                await sleep(1000);
            }


        }


    }


}



function addActionListeners(buttonIds) {
    buttonIds.forEach(buttonId => {
        document.getElementById(buttonId).addEventListener('click', function() {
            const action = this.id;  // 'this' refers to the button clicked
            sendAction(action);
        });
    });
}


// Initialize the listeners for your action buttons
addActionListeners(['print']);



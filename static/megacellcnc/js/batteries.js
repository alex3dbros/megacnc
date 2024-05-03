let capacityUpdateInterval;

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

function fetchCells(projectId) {
    $.ajax({
        url: '/get-cells',  // Your endpoint URL
        type: 'GET',
        data: { project_id: projectId },
        success: function(response) {
            // Assuming 'response' contains the cells data
            updateCellsList(response.cells);
        },
        error: function() {
            alert('Error fetching cells');
        }
    });
}

function updateCellsList(cells) {
    const cellsList = $('#left-list');  // Assuming you have a container to display cells
    cellsList.empty();  // Clear existing cells
    cells.forEach(function(cell) {

        var listItem = document.createElement('div');
        listItem.className = 'list-group-item';
        listItem.textContent = `${cell.id} - ${cell.capacity}`;
        listItem.dataset.itemId = `${cell.uuid}`;
        listItem.dataset.capacity = `${cell.capacity}`;

        cellsList.append(listItem);
    });
}

function createProjectDropdown(projects, selectedProjectName = "Select Project") {
    // Create the dropdown container
    let dropdownDiv = document.createElement('div');
    dropdownDiv.className = 'dropdown';

    // Create the button that toggles the dropdown
    let button = document.createElement('button');
    button.className = 'btn btn-default dropdown-toggle';
    button.setAttribute('type', 'button');
    button.setAttribute('data-bs-toggle', 'dropdown');
    button.textContent = selectedProjectName;

    // Create the dropdown menu
    let dropdownMenu = document.createElement('div');
    dropdownMenu.className = 'dropdown-menu';

    // Add 'All' option
    let allOption = document.createElement('a');
    allOption.className = 'dropdown-item';
    allOption.href = 'javascript:void(0);';
    allOption.textContent = 'All';
    allOption.onclick = function() {
        fetchCells('all');
        button.textContent = 'All'; // Update button text
    };
    dropdownMenu.appendChild(allOption);

    // Add project options
    projects.forEach(project => {
        let option = document.createElement('a');
        option.className = 'dropdown-item';
        option.href = 'javascript:void(0);';
        option.textContent = project.name;
        option.onclick = function() {
            fetchCells(project.id);
            button.textContent = project.name; // Update button text
        };
        dropdownMenu.appendChild(option);
    });

    // Assemble the dropdown
    dropdownDiv.appendChild(button);
    dropdownDiv.appendChild(dropdownMenu);

    return dropdownDiv;
}

function makeBatterySortable() {
    var lists = document.querySelectorAll('.sortable-cell');
    lists.forEach(list => {
        new Sortable(list, {
            group: {
                name: 'cells',
                pull: true,  // Allow pulling items out
                put: true    // Allow putting items in any list
            },
            animation: 150,
            revertOnSpill: true,

            onAdd: function (evt) {
                // If an item is added and there's already an item, swap or manage the items
                if (evt.to.children.length > 1) {
                    // Optional: Implement swapping logic if needed
                    let existingItem = evt.to.children[0];  // Assuming the first child is the existing item
                    evt.from.appendChild(existingItem);  // Move the existing item back to the origin
                }
                updatePlaceholderVisibility(evt.to);
            },
            onRemove: function (evt) {
                updatePlaceholderVisibility(evt.from);
                updateCapacityOnModification(evt);
            },

            onChange: function (evt) {
                console.log("Event 2");
                updateCapacityOnModification(evt);
            },

            onSort: function (evt) {
                // Called when an item is moved within the list or between lists
                updatePlaceholderVisibility(evt.to);
                if (evt.from !== evt.to) {
                    updatePlaceholderVisibility(evt.from);
                }
            }
        });
    });
}

function updatePlaceholderVisibility(list) {
    // Find the placeholder
    const placeholder = list.querySelector('.placeholder');
    // Adjust visibility based on the presence of actual items
    if (list.children.length === 0) {
        if (placeholder) placeholder.style.display = '';
    } else {
        if (placeholder) placeholder.style.display = 'none';
    }
}


function updateCapacityOnModification(event) {
    console.log("Event triggered:", event.type, "on:", event.to.id || event.from.id);
    let seriesIndex = event.to.dataset.series || event.from.dataset.series;  // Assuming data-series is set correctly
    console.log(seriesIndex);
    const seriesCells = document.querySelectorAll(`[data-series="${seriesIndex}"] .list-group-item`);
    console.log(seriesCells);
    let totalCapacity = 0;

    seriesCells.forEach(cell => {
        totalCapacity += parseFloat(cell.dataset.capacity);
        console.log(cell.dataset.capacity);
    });

    let capacityDisplay = document.getElementById(`capacity-${seriesIndex}`);
    capacityDisplay.textContent = `${totalCapacity.toFixed(2)} mAh`;
}


function fetchAndPopulateCells(batteryId) {
    fetch(`/get-battery-cells/?bat_id=${batteryId}`)
    .then(response => response.json())
    .then(data => {
        data.cells.forEach(cell => {
            const slotId = cell.bat_position;  // Using bat_position directly from the response
            const slot = document.getElementById(slotId);
            if (slot) {
                const listItem = document.createElement('li');
                listItem.textContent = `${cell.id} - ${cell.capacity}`;
                listItem.className = 'list-group-item';
                listItem.dataset.itemId = cell.uuid; // Use UUID instead of serial number as itemId
                listItem.dataset.capacity = cell.capacity;
                slot.appendChild(listItem);
            }
        });
        updateAllCapacities();  // This function needs to be defined to update capacities based on cells added.
    })
    .catch(error => console.error('Failed to fetch cells:', error));
}




function updateAllCapacities() {
    const seriesElements = document.querySelectorAll('[data-series]');
    seriesElements.forEach(series => {
        const seriesId = series.dataset.series;
        updateSeriesCapacityById(seriesId);
    });

    // Count the cells in the middle-list
    const middleListCellsCount = document.querySelectorAll('#middle-list .list-group-item').length;
    // Update the h4 text
    const transferCellsTitle = document.getElementById('transfer-cells-title');
    transferCellsTitle.textContent = `Transfer Cells (${middleListCellsCount})`; // Display count
}


function updateSeriesCapacityById(seriesId) {
    const cells = document.querySelectorAll(`[data-series="${seriesId}"] .list-group-item`);
    let totalCapacity = 0;

    cells.forEach(cell => {
        totalCapacity += parseFloat(cell.dataset.capacity || 0);
    });

    const capacityDisplay = document.getElementById(`capacity-${seriesId}`);
    capacityDisplay.textContent = `${totalCapacity.toFixed(2)} mAh`;
}


function createBatteryLayout(series, parallel, batteryId) {
    const container = document.createElement('div');
    container.className = 'col-md-4';
    container.innerHTML = `<h4 class="text-center">Battery Pack Layout</h4>`;

    const table = document.createElement('table');
    table.className = 'table';

    const tbody = document.createElement('tbody');
    table.appendChild(tbody);

    for (let i = 0; i < series; i++) {
        const tr = document.createElement('tr');
        const rowNumberCell = document.createElement('td');
        rowNumberCell.textContent = i + 1;
        rowNumberCell.className = 'text-center';
        tr.appendChild(rowNumberCell);

        for (let j = 0; j < parallel; j++) {
            const td = document.createElement('td');
            const cellList = document.createElement('ul');
            cellList.className = 'sortable-cell';
            cellList.id = `cell-${i + 1}${String.fromCharCode(65 + j)}`;
            cellList.dataset.series = i + 1; // Keep track of series for each cell container

            // Event listener setup (assuming SortableJS or similar)
            //setupCellListeners(cellList);

            td.appendChild(cellList);
            tr.appendChild(td);
        }

        const capacityCell = document.createElement('td');
        capacityCell.className = 'text-center capacity-display';
        capacityCell.id = `capacity-${i + 1}`;
        capacityCell.textContent = "0 mAh";
        tr.appendChild(capacityCell);

        tbody.appendChild(tr);
    }

    container.appendChild(table);

    if (batteryId) {
        fetchAndPopulateCells(batteryId);
    }

    return container;
}

function setupCellListeners(cellList) {
    console.log("Setting up listeners for:", cellList.id);
    new Sortable(cellList, {
        group: 'cells',
        animation: 150,
        onAdd: function (/**Event*/evt) {
            console.log("something");
        },
        onRemove: function(evt) { updateCapacityOnModification(evt); },
        onUpdate: function(evt) { updateCapacityOnModification(evt); }
    });
}




function highlightCell(fullUuid, required_cells_count) {
    // Remove existing highlights and prepare for a possible move
    document.querySelectorAll('.highlight').forEach(cell => {
        cell.classList.remove('highlight');
    });

    if (!fullUuid) return; // Exit if input is empty

    // Split the fullUuid to extract the uuid part before '-C'
    const uuidParts = fullUuid.split('-C');
    const uuid = uuidParts[0]; // This assumes the format "D20240502-S000093-C3050-mAh" and takes only the first part

    let neededItemsCount = calculateNeededItems(required_cells_count);
    const cells = document.querySelectorAll('.list-group-item');
    cells.forEach(cell => {
        if (cell.getAttribute('data-item-id') === uuid) {
            cell.classList.add('highlight'); // Highlight the cell
            cell.parentNode.prepend(cell); // Move to the top of its current list

            // If the item is in the left-list and needed items are still required
            if (cell.parentNode.id === 'left-list' && neededItemsCount > 0) {
                document.getElementById('middle-list').appendChild(cell); // Move the item to the middle-list
                neededItemsCount--; // Decrement the count of needed items
            }
        }
    });
}



function calculateNeededItems(required_cells_count) {
    const middleListCells = document.querySelectorAll('#middle-list .list-group-item').length;
    const batteryPackCells = document.querySelectorAll('#battery-pack-container .list-group-item').length; // Adjust selector based on your actual structure

    const alreadyPlacedCells = middleListCells + batteryPackCells;
    return Math.max(required_cells_count - alreadyPlacedCells, 0);
}

function updateLeftListUI() {
    // Optional: Any UI updates after transferring items
}



$('#batteries-tbl').on('click', '.expandBtn', function() {

    var $allAccordions = $('.accordion-content');


    var $triggerRow = $(this).closest('tr'); // The row where the button was clicked
    var $nextRow = $triggerRow.next('.accordion-content'); // The next row, which might be the accordion content


    var batteryId = $(this).data('battery-id');
    var UUID = $(this).data('battery-uuid');
    var projects = $(this).data('projects');
    var series = $(this).data('series');
    var parallel = $(this).data('parallel');
    var required_cells_count = series * parallel

    // Hide and remove all other accordion contents except for the current one
    $allAccordions.not($nextRow).hide().remove();
    clearInterval(capacityUpdateInterval);
    if ($nextRow.length) {
        // Accordion row exists, toggle its visibility
        $nextRow.toggle();

        if (!$nextRow.is(':visible')) {
            $nextRow.remove();

        }


    } else {
        console.log("Creating tab");
        var leftListId = `left-list`;
        var middleListId = `middle-list`;
        // Accordion row does not exist, create and inject it with dynamic slot number in the ID
        var colspan = $triggerRow.children('td').length; // Number of columns in the row
        var accordionRow = `
            <tr class="accordion-content" data-battery-number="${batteryId}">
                <td colspan="${colspan}">
                    <div class="container-fluid">
                        <div class="row">
                            <!-- Project Selection and List of Cells -->
                            <div class="col-md-2">
                            
                                <div id="dropdown-container">
                                    <!-- Dynamic dropdown will be inserted here by JavaScript -->
                                </div>
                                
                                <div id="${leftListId}" class="list-group">
                                    <!-- Items will be dynamically inserted here -->
                                </div>
                                
                                <div class="control-panel">
                                    <input type="number" id="min-capacity-input" class="form-control" style="width: auto; display: inline-block; margin-top:10px; margin-right: 5px;" placeholder="Min Capacity (mAh)">
                                    <input type="number" id="max-capacity-input" class="form-control" style="width: auto; display: inline-block; margin-top:10px;" placeholder="Max Capacity (mAh)">
                                    <button class="btn btn-light" id="auto-select-btn" style="margin-top: 10px;">Auto Select</button>
                                </div>


                            </div>
                            
                            <!-- Transfer List -->
                            <div class="col-md-2">
                                <h4 id="transfer-cells-title" class="text-center">Transfer Cells</h4>

                                <div id="${middleListId}" class="list-group">
                                    <!-- Items moved from left list will appear here -->
                                </div>
                                <button id="assign-btn" class="btn btn-light" style="margin-top: 10px;">Assign</button>

                            </div>
                            
                            <div class="col-md-8">
                            <!-- Battery Pack Visualization -->
                                <div class="col-md-4">

                                    <h4 class="text-center">Search by UUID</h4>
                                    <input type="text" id="uuid-search" class="form-control" placeholder="Enter UUID">
                                    <div id="battery-controls">

                                        <button class="btn btn-light" id="reset-btn" style="margin-top: 10px;">Reset Cells</button>
                                        <button class="btn btn-light" id="save-btn" style="margin-top: 10px; margin-left: 10px;">Save Pack</button>
                                    </div>
                                    
                                </div>
                            
                            
                                <div id="battery-pack-container">
                                    <!-- Dynamic dropdown will be inserted here by JavaScript -->
                                </div>
                                


                                
                            </div>
                        </div>
                    </div>
                </td>
                </tr>

        `;

    // Insert accordion and initialize Sortable
    $(accordionRow).insertAfter($triggerRow).show(function() {
        new Sortable(document.getElementById(leftListId), { group: 'shared', animation: 150 });
        new Sortable(document.getElementById(middleListId), { group: 'shared', animation: 150 });

        let accordionContent = document.getElementById('accordion-content-id');
        console.log(projects);
        let dropdown  = createProjectDropdown(projects);
        document.getElementById('dropdown-container').appendChild(dropdown);

        const batteryLayout = createBatteryLayout(series, parallel, batteryId);
        document.getElementById('battery-pack-container').appendChild(batteryLayout);
        makeBatterySortable();

        const searchInput = document.getElementById('uuid-search');

        console.log(searchInput);

        // Listen for input events for real-time feedback and keypress to handle Enter
        searchInput.addEventListener('input', function() {
            const uuid = this.value.trim();
            highlightCell(uuid, required_cells_count);
        });

        searchInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();  // Prevent any default action associated with the Enter key
                const uuid = this.value.trim();
                console.log(uuid);
                highlightCell(uuid, required_cells_count);
                this.select();
            }
        });


        document.getElementById('auto-select-btn').addEventListener('click', function() {
            const minCapacity = parseFloat(document.getElementById('min-capacity-input').value);
            const maxCapacity = parseFloat(document.getElementById('max-capacity-input').value);
            const leftListItems = document.querySelectorAll('#left-list .list-group-item');
            const middleList = document.getElementById('middle-list');
            let neededItemsCount = calculateNeededItems(required_cells_count);

            leftListItems.forEach(item => {
                let itemCapacity = parseFloat(item.dataset.capacity);
                if ((itemCapacity >= minCapacity && itemCapacity <= maxCapacity) && neededItemsCount > 0) {
                    middleList.appendChild(item); // This moves the item, not just cloning
                    neededItemsCount--; // Decrement the needed items count
                }
            });

            updateLeftListUI(); // Optional: Update the UI if needed

        });

    document.getElementById('assign-btn').addEventListener('click', function() {
        assignCellsToPack(series, parallel);
    });

    capacityUpdateInterval = setInterval(updateAllCapacities, 1000);


    document.getElementById('reset-btn').addEventListener('click', function() {
        const slots = document.querySelectorAll('.sortable-cell');
        const middleList = document.getElementById('middle-list');

        slots.forEach(slot => {
            // Move each cell in the slot back to the middle list
            while (slot.firstChild) {
                middleList.appendChild(slot.firstChild);
            }
        });

        updateAllCapacities(); // Update capacities if necessary
    });

    document.getElementById('save-btn').addEventListener('click', function() {
        const cellsData = [];
        const seriesSlots = document.querySelectorAll('.sortable-cell');

        seriesSlots.forEach(slot => {
            const cells = slot.querySelectorAll('.list-group-item');
            cells.forEach(cell => {
                cellsData.push({
                    cellId: cell.dataset.itemId,
                    slotId: slot.id,
                    capacity: cell.dataset.capacity
                });
            });
        });

        const payload = {
            batteryId: batteryId,
            cellsData: cellsData
        };

        // AJAX Request to save data
        fetch('/save-battery-configuration/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') // Ensure CSRF token is included if needed
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            toastr.success('Pack configuration saved successfully!', "Success");
        })
        .catch((error) => {
            console.error('Error:', error);
            toastr.error("Error saving pack configuration", "Error");
        });
    });






    });


    }

    //initializeChart( -1, cellId);

});

// Assign Cells to pack
function assignCellsToPack(series, parallel) {
    const cells = Array.from(document.querySelectorAll('#middle-list .list-group-item'));
    const requiredCells = series * parallel;

    cells.sort((a, b) => parseFloat(b.dataset.capacity) - parseFloat(a.dataset.capacity));

    let seriesArrays = Array.from({ length: series }, () => []);

    // Two-way selection for initial fill
    let highIndex = 0, lowIndex = cells.length - 1;
    for (let i = 0; i < series; i++) {
        while (seriesArrays[i].length < parallel && highIndex <= lowIndex) {
            seriesArrays[i].push(cells[highIndex++]); // Add high capacity cell
            if (seriesArrays[i].length < parallel && highIndex <= lowIndex) {
                seriesArrays[i].push(cells[lowIndex--]); // Add low capacity cell
            }
        }
    }

    // Calculate initial total capacities per series
    let capacities = seriesArrays.map(s => s.reduce((total, cell) => total + parseFloat(cell.dataset.capacity), 0));

    // Perform iterative balancing
    for (let a = 0; a < series; a++) {
        for (let b = a + 1; b < series; b++) {
            // Attempt to swap cells between series a and b to minimize variance
            for (let i = 0; i < parallel; i++) {
                for (let j = 0; j < parallel; j++) {
                    // Calculate potential new capacities after a swap
                    let newCapacityA = capacities[a] - parseFloat(seriesArrays[a][i].dataset.capacity) + parseFloat(seriesArrays[b][j].dataset.capacity);
                    let newCapacityB = capacities[b] - parseFloat(seriesArrays[b][j].dataset.capacity) + parseFloat(seriesArrays[a][i].dataset.capacity);

                    // Calculate current and new variances
                    let currentVariance = Math.abs(capacities[a] - capacities[b]);
                    let newVariance = Math.abs(newCapacityA - newCapacityB);

                    // If the new variance is smaller, perform the swap
                    if (newVariance < currentVariance) {
                        let temp = seriesArrays[a][i];
                        seriesArrays[a][i] = seriesArrays[b][j];
                        seriesArrays[b][j] = temp;

                        // Update capacities
                        capacities[a] = newCapacityA;
                        capacities[b] = newCapacityB;
                    }
                }
            }
        }
    }

    // Move cells to the corresponding slots
    for (let i = 0; i < series; i++) {
        for (let j = 0; j < parallel; j++) {
            const slotId = `cell-${i + 1}${String.fromCharCode(65 + j)}`;
            const slot = document.getElementById(slotId);
            slot.innerHTML = ''; // Clear existing content
            slot.appendChild(seriesArrays[i][j]); // Assign new cell
        }
    }
}



function updateUIAfterAssignment() {
    // Example UI update
    document.getElementById('assign-btn').disabled = true; // Disable button after assignment
}






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



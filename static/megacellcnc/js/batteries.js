let capacityUpdateInterval;
let currentBatteryId = null;  // Stores the currently open battery ID

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
    const leftList = document.getElementById('left-list');
    if (leftList) {
        leftList.innerHTML = '<div class="text-center p-2"><i class="fa fa-spinner fa-spin"></i></div>';
    }
    
    $.ajax({
        url: '/get-cells',
        type: 'GET',
        data: { project_id: projectId },
        success: function(response) {
            updateCellsList(response.cells);
            updateAvailableCount();
        },
        error: function() {
            if (leftList) leftList.innerHTML = '<div class="text-danger p-2">Fehler</div>';
        }
    });
}

// Extract Cell-ID from UUID (e.g. "D20230620-S012559" -> "012559")
function extractCellId(uuid) {
    const match = uuid.match(/-S(\d+)/);
    return match ? match[1] : uuid;
}

function updateCellsList(cells) {
    const cellsList = $('#left-list');
    cellsList.empty();
    cells.forEach(function(cell) {
        var listItem = document.createElement('div');
        listItem.className = 'list-group-item';
        const cellId = extractCellId(cell.uuid);
        listItem.textContent = `${cellId} - ${cell.capacity} mAh - ${cell.esr} mΩ`;
        listItem.dataset.itemId = `${cell.uuid}`;
        listItem.dataset.cellId = cellId;
        listItem.dataset.capacity = `${cell.capacity}`;
        listItem.dataset.esr = `${cell.esr}`;
        listItem.dataset.voltage = `${cell.voltage}`;
        cellsList.append(listItem);
    });
}

function populateProjectDropdown(projects) {
    const select = document.getElementById('project-dropdown');
    if (!select) return;
    
    // Add 'All' option
    const allOption = document.createElement('option');
    allOption.value = 'all';
    allOption.textContent = 'Alle Projekte';
    allOption.selected = true;
    select.appendChild(allOption);
    
    // Add project options
    projects.forEach(project => {
        const option = document.createElement('option');
        option.value = project.id;
        option.textContent = project.name;
        select.appendChild(option);
    });
    
    // Event listener for selection change
    select.addEventListener('change', function() {
        fetchCells(this.value);
    });
    
    // Initial load
    fetchCells('all');
}

function updateAvailableCount() {
    const count = document.querySelectorAll('#left-list .list-group-item').length;
    const badge = document.getElementById('available-count');
    if (badge) badge.textContent = count;
}

function updateTransferCount() {
    const count = document.querySelectorAll('#middle-list .list-group-item').length;
    const badge = document.getElementById('transfer-count');
    if (badge) badge.textContent = count;
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


// Convert old slot ID format (cell-1A) to new format (cell-1-1)
function convertSlotId(oldId) {
    // Match old format: cell-1A, cell-2B, etc.
    const match = oldId.match(/^cell-(\d+)([A-Z]+)$/);
    if (match) {
        const series = match[1];
        const parallelLetter = match[2];
        const parallelNum = parallelLetter.charCodeAt(0) - 64; // A=1, B=2, etc.
        return `cell-${series}-${parallelNum}`;
    }
    return oldId; // Already in new format or unknown
}

function fetchAndPopulateCells(batteryId) {
    fetch(`/get-battery-cells/?bat_id=${batteryId}`)
    .then(response => response.json())
    .then(data => {
        data.cells.forEach(cell => {
            // Support both old (cell-1A) and new (cell-1-1) format
            let slotId = convertSlotId(cell.bat_position);
            let slot = document.getElementById(slotId);
            
            if (slot) {
                const listItem = document.createElement('li');
                const cellId = extractCellId(cell.uuid);
                listItem.textContent = `${cellId}`;
                listItem.className = 'list-group-item';
                listItem.dataset.itemId = cell.uuid;
                listItem.dataset.cellId = cellId;
                listItem.dataset.capacity = cell.capacity;
                listItem.dataset.esr = cell.esr;
                listItem.dataset.voltage = cell.voltage;
                listItem.title = `${cell.capacity} mAh | ${cell.esr} mΩ`;
                slot.appendChild(listItem);
            }
        });
        updateAllCapacities();
    })
    .catch(error => console.error('Failed to fetch cells:', error));
}




function updateAllCapacities() {
    const seriesElements = document.querySelectorAll('[data-series]');
    seriesElements.forEach(series => {
        const seriesId = series.dataset.series;
        updateSeriesCapacityById(seriesId);
    });

    // Update counters
    updateAvailableCount();
    updateTransferCount();
}


function updateSeriesCapacityById(seriesId) {
    const cells = document.querySelectorAll(`[data-series="${seriesId}"] .list-group-item`);
    let totalCapacity = 0;

    cells.forEach(cell => {
        totalCapacity += parseFloat(cell.dataset.capacity || 0);
    });

    const capacityDisplay = document.getElementById(`capacity-${seriesId}`);
    if (capacityDisplay) {
        capacityDisplay.textContent = `${totalCapacity.toFixed(2)} mAh`;
    }
}


function createBatteryLayout(series, parallel, batteryId) {
    const container = document.createElement('div');
    container.className = 'w-100';
    
    const totalCells = series * parallel;
    container.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0"><i class="fa fa-battery-full me-2"></i>Battery Pack (${series}S${parallel}P = ${totalCells} Zellen)</h5>
            <span class="badge bg-info">Kapazität links | Zellen rechts scrollbar</span>
        </div>
    `;

    // Create wrapper for horizontal scroll if many parallel cells
    const scrollWrapper = document.createElement('div');
    scrollWrapper.className = 'battery-scroll-wrapper';
    
    const layoutDiv = document.createElement('div');
    layoutDiv.className = 'battery-grid-layout';

    for (let i = 0; i < series; i++) {
        const seriesRow = document.createElement('div');
        seriesRow.className = 'series-row';
        
        // Fixed left part: Capacity + Series label
        const fixedPart = document.createElement('div');
        fixedPart.className = 'series-fixed';
        fixedPart.innerHTML = `
            <div class="capacity-display" id="capacity-${i + 1}">0 mAh</div>
            <div class="series-label">S${i + 1}</div>
        `;
        seriesRow.appendChild(fixedPart);
        
        // Scrollable part: Cell slots
        const cellsContainer = document.createElement('div');
        cellsContainer.className = 'cells-container';
        
        for (let j = 0; j < parallel; j++) {
            const cellSlot = document.createElement('div');
            cellSlot.className = 'cell-slot';
            
            const cellList = document.createElement('ul');
            cellList.className = 'sortable-cell';
            // Use numeric index for large parallel counts
            cellList.id = `cell-${i + 1}-${j + 1}`;
            cellList.dataset.series = i + 1;
            cellList.title = `S${i + 1} P${j + 1}`;
            
            const label = document.createElement('span');
            label.className = 'slot-label';
            label.textContent = `P${j + 1}`;
            
            cellSlot.appendChild(label);
            cellSlot.appendChild(cellList);
            cellsContainer.appendChild(cellSlot);
        }
        
        seriesRow.appendChild(cellsContainer);
        layoutDiv.appendChild(seriesRow);
    }

    scrollWrapper.appendChild(layoutDiv);
    container.appendChild(scrollWrapper);

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
    var batteryName = $(this).data('battery-name');
    var projects = $(this).data('projects');
    var series = $(this).data('series');
    var parallel = $(this).data('parallel');
    var required_cells_count = series * parallel;
    
    // Store battery ID globally for replacement logging
    currentBatteryId = batteryId;

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
                    <div class="pack-editor">
                        <!-- Compact Control Bar -->
                        <div class="control-bar">
                            <div class="control-group">
                                <label>Projekt</label>
                                <select id="project-dropdown" class="form-select form-select-sm"></select>
                            </div>
                            <div class="control-group">
                                <label>mAh Filter</label>
                                <div class="d-flex gap-1">
                                    <input type="number" id="min-capacity-input" class="form-control form-control-sm" placeholder="Min" style="width:65px">
                                    <input type="number" id="max-capacity-input" class="form-control form-control-sm" placeholder="Max" style="width:65px">
                                </div>
                            </div>
                            <div class="info-group">
                                <span class="info-label">Verfügbar:</span>
                                <span class="badge bg-secondary" id="available-count">0</span>
                            </div>
                            <div class="info-group transfer-toggle" id="transfer-toggle">
                                <span class="info-label">Transfer:</span>
                                <span class="badge bg-success" id="transfer-count">0</span>
                                <i class="fa fa-chevron-down ms-1"></i>
                            </div>
                            <div class="control-buttons">
                                <button class="btn btn-primary btn-sm" id="auto-select-btn" title="Auto-Select"><i class="fa fa-magic"></i></button>
                                <button class="btn btn-success btn-sm" id="assign-btn" title="Assign"><i class="fa fa-check"></i></button>
                                <button class="btn btn-warning btn-sm" id="reset-btn" title="Reset"><i class="fa fa-undo"></i></button>
                                <button class="btn btn-primary btn-sm" id="save-btn" title="Save"><i class="fa fa-save"></i></button>
                                <button class="btn btn-info btn-sm" id="chart-btn" title="Grafik anzeigen"><i class="fa fa-line-chart"></i></button>
                                <button class="btn btn-secondary btn-sm" id="history-btn" title="Ersetzungs-Historie"><i class="fa fa-history"></i></button>
                                <button class="btn btn-secondary btn-sm" id="print-pack-btn" title="Labels drucken"><i class="fa fa-print"></i></button>
                                <button class="btn btn-secondary btn-sm" id="export-pack-btn" title="Zellenliste exportieren"><i class="fa fa-download"></i></button>
                                <button class="btn btn-danger btn-sm" id="dissolve-btn" title="Pack auflösen"><i class="fa fa-trash"></i></button>
                            </div>
                        </div>
                        
                        <!-- Workflow Indicator -->
                        <div id="workflow-indicator" class="workflow-indicator">
                            <div class="workflow-step" id="step-select" data-step="1">
                                <span class="step-icon">①</span> Zellen wählen
                            </div>
                            <span class="workflow-arrow">→</span>
                            <div class="workflow-step" id="step-auto" data-step="2">
                                <span class="step-icon">②</span> Auto-Select
                            </div>
                            <span class="workflow-arrow">→</span>
                            <div class="workflow-step" id="step-assign" data-step="3">
                                <span class="step-icon">③</span> Assign
                            </div>
                            <span class="workflow-arrow">→</span>
                            <div class="workflow-step" id="step-save" data-step="4">
                                <span class="step-icon">④</span> Speichern
                            </div>
                            <div id="unsaved-indicator" class="unsaved-indicator">
                                <i class="fa fa-exclamation-triangle"></i> Nicht gespeichert
                            </div>
                        </div>
                        
                        <!-- Status Display -->
                        <div id="assign-status" class="assign-status" style="display:none;">
                            <div class="status-content">
                                <i class="fa fa-cog fa-spin me-2"></i>
                                <span id="status-text">Initialisiere...</span>
                            </div>
                            <div class="progress mt-2" style="height:4px;">
                                <div id="status-progress" class="progress-bar bg-success" style="width:0%"></div>
                            </div>
                        </div>
                        
                        <!-- Result Banner (shown after balancing) -->
                        <div id="result-banner" class="result-banner" style="display:none;"></div>
                        
                        <!-- Hidden Transfer List (collapsible) -->
                        <div id="transfer-panel" class="transfer-panel" style="display:none;">
                            <div id="${middleListId}" class="list-group cell-list"></div>
                        </div>
                        
                        <!-- Hidden source list for cells -->
                        <div id="${leftListId}" class="list-group" style="display:none;"></div>
                        
                        <!-- Battery Pack Layout -->
                        <div class="pack-section">
                            <div id="battery-pack-container"></div>
                        </div>
                    </div>
                    
                    <!-- Chart Modal -->
                    <div id="chart-modal-overlay" class="chart-modal-overlay">
                        <div class="chart-modal">
                            <div class="chart-modal-header">
                                <span class="chart-modal-title"><i class="fa fa-line-chart me-2"></i>Pack Analyse - ${series}S${parallel}P</span>
                                <button class="chart-modal-close" id="chart-modal-close">&times;</button>
                            </div>
                            <div class="chart-modal-body">
                                <div class="series-selector" id="series-selector"></div>
                                <div class="chart-controls" id="chart-controls"></div>
                                <div class="chart-container">
                                    <canvas id="pack-chart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        `;

    // Insert accordion and initialize Sortable
    $(accordionRow).insertAfter($triggerRow).show(function() {
        new Sortable(document.getElementById(leftListId), { 
            group: 'shared', 
            animation: 150,
            onAdd: function() { updateAvailableCount(); updateTransferCount(); },
            onRemove: function() { updateAvailableCount(); updateTransferCount(); }
        });
        new Sortable(document.getElementById(middleListId), { 
            group: 'shared', 
            animation: 150,
            onAdd: function() { updateTransferCount(); },
            onRemove: function() { updateTransferCount(); }
        });

        // Initialize project dropdown
        populateProjectDropdown(projects);

        const batteryLayout = createBatteryLayout(series, parallel, batteryId);
        document.getElementById('battery-pack-container').appendChild(batteryLayout);
        makeBatterySortable();

        // Transfer panel toggle
        document.getElementById('transfer-toggle').addEventListener('click', function() {
            const panel = document.getElementById('transfer-panel');
            const icon = this.querySelector('i');
            if (panel.style.display === 'none') {
                panel.style.display = 'block';
                icon.className = 'fa fa-chevron-up ms-1';
            } else {
                panel.style.display = 'none';
                icon.className = 'fa fa-chevron-down ms-1';
            }
        });

        document.getElementById('auto-select-btn').addEventListener('click', function() {
            const minCapacity = parseFloat(document.getElementById('min-capacity-input').value) || 0;
            const maxCapacity = parseFloat(document.getElementById('max-capacity-input').value) || 99999;
            const leftListItems = Array.from(document.querySelectorAll('#left-list .list-group-item'));
            const middleList = document.getElementById('middle-list');
            let neededItemsCount = calculateNeededItems(required_cells_count);

            // Phase A: Filter valid candidates
            let validCandidates = leftListItems.filter(item => {
                let cap = parseFloat(item.dataset.capacity);
                return cap >= minCapacity && cap <= maxCapacity;
            });

            // Sort: capacity ascending, then ESR descending (worst to best)
            validCandidates.sort((a, b) => {
                let capDiff = parseFloat(a.dataset.capacity) - parseFloat(b.dataset.capacity);
                if (capDiff !== 0) return capDiff;
                return parseFloat(b.dataset.esr) - parseFloat(a.dataset.esr);
            });

            // Equidistant sampling for representative selection
            if (validCandidates.length >= neededItemsCount && neededItemsCount > 0) {
                const step = validCandidates.length / neededItemsCount;
                for (let i = 0; i < neededItemsCount; i++) {
                    const index = Math.floor(i * step);
                    middleList.appendChild(validCandidates[index]);
                }
            } else {
                // Not enough cells - take all valid candidates
                validCandidates.forEach(item => {
                    if (neededItemsCount > 0) {
                        middleList.appendChild(item);
                        neededItemsCount--;
                    }
                });
            }

            updateLeftListUI();
            updateAllCapacities();
            
            // Update workflow step
            setWorkflowStep(3); // Ready for Assign
            toastr.info(`${required_cells_count - calculateNeededItems(required_cells_count)} Zellen ausgewählt`, 'Auto-Select');
        });

    document.getElementById('assign-btn').addEventListener('click', function() {
        setWorkflowStep(3); // Assign in progress
        const btn = this;
        const spinner = document.getElementById('assign-spinner');
        const originalText = btn.innerHTML;
        
        // Show loading state
        btn.disabled = true;
        btn.innerHTML = '<i class="fa fa-cog fa-spin"></i>';
        
        // Run async assignment
        (async function() {
            try {
                await assignCellsToPack(series, parallel);
                toastr.success('Zellen erfolgreich verteilt!', 'Balancing abgeschlossen');
            } catch (error) {
                console.error('Assign error:', error);
                toastr.error('Fehler beim Zuweisen: ' + error.message, 'Fehler');
                hideStatus();
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa fa-check"></i>';
            }
        })();
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

    // Chart Button
    document.getElementById('chart-btn').addEventListener('click', function() {
        openPackChart(series, parallel);
    });
    
    // Chart Modal Close
    document.getElementById('chart-modal-close').addEventListener('click', function() {
        closePackChart();
    });
    
    // Close modal on overlay click
    document.getElementById('chart-modal-overlay').addEventListener('click', function(e) {
        if (e.target === this) {
            closePackChart();
        }
    });

    // History Button
    document.getElementById('history-btn').addEventListener('click', function() {
        openReplacementHistory(batteryId);
    });

    // Print Pack Button
    document.getElementById('print-pack-btn').addEventListener('click', function() {
        printPackLabels();
    });

    // Export Pack Button
    document.getElementById('export-pack-btn').addEventListener('click', function() {
        exportPackCells(batteryName);
    });

    // Pack auflösen Button
    document.getElementById('dissolve-btn').addEventListener('click', function() {
        // Count current cells in pack
        const cellsInPack = document.querySelectorAll('.sortable-cell .list-group-item').length;
        
        if (cellsInPack === 0) {
            toastr.info('Pack ist bereits leer', 'Info');
            return;
        }
        
        // Show confirmation dialog
        const confirmed = confirm(
            `⚠️ Pack wirklich auflösen?\n\n` +
            `${cellsInPack} Zellen werden freigegeben und\n` +
            `stehen wieder zur Verfügung.\n\n` +
            `Diese Aktion kann nicht rückgängig gemacht werden.`
        );
        
        if (!confirmed) return;
        
        // Send empty cellsData to backend to release all cells
        const payload = {
            batteryId: batteryId,
            cellsData: []  // Empty = release all cells
        };
        
        fetch('/save-battery-configuration/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Pack dissolved:', data);
            
            // Clear all slots visually
            document.querySelectorAll('.sortable-cell').forEach(slot => {
                slot.innerHTML = '';
                slot.classList.remove('cell-done', 'cell-placed');
            });
            
            // Clear transfer list
            document.getElementById('middle-list').innerHTML = '';
            
            // Update UI
            updateAllCapacities();
            markSaved();
            hideResultBanner();
            setWorkflowStep(1);
            
            toastr.success(`${cellsInPack} Zellen wurden freigegeben`, 'Pack aufgelöst');
        })
        .catch((error) => {
            console.error('Error:', error);
            toastr.error('Fehler beim Auflösen des Packs', 'Fehler');
        });
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
            toastr.success('Pack erfolgreich gespeichert!', "Gespeichert");
            markSaved();
            hideResultBanner();
        })
        .catch((error) => {
            console.error('Error:', error);
            toastr.error("Fehler beim Speichern", "Fehler");
        });
    });






    });


    }

    //initializeChart( -1, cellId);

});

// Helper: Calculate parallel resistance (1 / sum(1/R))
function calculateGroupResistance(cellsArray) {
    const sumInverseR = cellsArray.reduce((sum, cell) => {
        const esr = parseFloat(cell.dataset.esr) || 1;
        return sum + (1 / esr);
    }, 0);
    return sumInverseR > 0 ? 1 / sumInverseR : 0;
}

// Helper: Calculate standard deviation
function calculateStdDev(values) {
    if (values.length === 0) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map(v => Math.pow(v - mean, 2));
    return Math.sqrt(squaredDiffs.reduce((a, b) => a + b, 0) / values.length);
}

// Helper: Calculate group capacity
function calculateGroupCapacity(cellsArray) {
    return cellsArray.reduce((total, cell) => total + parseFloat(cell.dataset.capacity), 0);
}

// Multi-Objective Score: weighted combination of capacity and resistance deviation
function calculateBalancingScore(seriesArrays, w1 = 0.6, w2 = 0.4) {
    const capacities = seriesArrays.map(s => calculateGroupCapacity(s));
    const resistances = seriesArrays.map(s => calculateGroupResistance(s));
    
    const stdDevCap = calculateStdDev(capacities);
    const stdDevRes = calculateStdDev(resistances);
    
    // Normalize: capacity in mAh (thousands), resistance in mOhm (small numbers)
    const normalizedCapScore = stdDevCap / 100; // Scale down
    const normalizedResScore = stdDevRes * 100; // Scale up
    
    return (w1 * normalizedCapScore) + (w2 * normalizedResScore);
}

// Status update helper
function updateStatus(phase, text, progress) {
    const statusDiv = document.getElementById('assign-status');
    const statusText = document.getElementById('status-text');
    const progressBar = document.getElementById('status-progress');
    
    if (statusDiv) statusDiv.style.display = 'block';
    if (statusText) {
        statusText.innerHTML = `<span class="phase-label">${phase}</span>${text}`;
    }
    if (progressBar) progressBar.style.width = progress + '%';
}

function hideStatus() {
    const statusDiv = document.getElementById('assign-status');
    if (statusDiv) statusDiv.style.display = 'none';
}

// Async delay for UI updates
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================
// WORKFLOW MANAGEMENT
// ============================================
let hasUnsavedChanges = false;

function setWorkflowStep(stepNumber) {
    document.querySelectorAll('.workflow-step').forEach(step => {
        const num = parseInt(step.dataset.step);
        step.classList.remove('completed', 'active');
        if (num < stepNumber) {
            step.classList.add('completed');
        } else if (num === stepNumber) {
            step.classList.add('active');
        }
    });
}

function markUnsaved() {
    hasUnsavedChanges = true;
    const indicator = document.getElementById('unsaved-indicator');
    const saveBtn = document.getElementById('save-btn');
    if (indicator) indicator.classList.add('visible');
    if (saveBtn) saveBtn.classList.add('needs-save');
}

function markSaved() {
    hasUnsavedChanges = false;
    const indicator = document.getElementById('unsaved-indicator');
    const saveBtn = document.getElementById('save-btn');
    if (indicator) indicator.classList.remove('visible');
    if (saveBtn) saveBtn.classList.remove('needs-save');
    setWorkflowStep(5); // Beyond last step = all done
}

function showResultBanner(stats) {
    const banner = document.getElementById('result-banner');
    if (!banner) return;
    
    banner.innerHTML = `
        <div class="result-header">
            <i class="fa fa-check-circle result-icon"></i>
            <span class="result-title">Balancing abgeschlossen!</span>
        </div>
        <div class="result-stats">
            <div class="stat-item">
                <span class="stat-value">${stats.cells}</span>
                <span class="stat-label">Zellen</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">${stats.iterations}</span>
                <span class="stat-label">Iterationen</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">${stats.swaps}</span>
                <span class="stat-label">Swaps</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">σ ${stats.stdDev}</span>
                <span class="stat-label">mAh Abweichung</span>
            </div>
        </div>
        <div class="result-actions">
            <button class="btn btn-action btn-save-now" onclick="document.getElementById('save-btn').click()">
                <i class="fa fa-save"></i> Jetzt Speichern
            </button>
            <button class="btn btn-action btn-outline-light" onclick="document.getElementById('reset-btn').click(); hideResultBanner();">
                <i class="fa fa-undo"></i> Neu verteilen
            </button>
            <button class="btn btn-action btn-outline-secondary" onclick="hideResultBanner()">
                <i class="fa fa-times"></i> Schließen
            </button>
        </div>
    `;
    banner.style.display = 'block';
    
    // Mark as unsaved and update workflow
    markUnsaved();
    setWorkflowStep(4); // Step 4: Save
}

function hideResultBanner() {
    const banner = document.getElementById('result-banner');
    if (banner) banner.style.display = 'none';
}

// ============================================
// CHART FUNCTIONALITY
// ============================================
let packChart = null;
let chartDatasets = {};
let selectedSeriesSet = new Set(); // Multi-select
let totalSeriesCount = 0;

const chartColors = {
    capacity: { color: '#4ecca3', label: 'Kapazität (mAh)' },
    esr: { color: '#e74c3c', label: 'ESR (mΩ)' },
    voltage: { color: '#3498db', label: 'Spannung (V)' }
};

// Different colors for each series
const seriesColors = [
    '#4ecca3', '#e74c3c', '#3498db', '#f39c12', '#9b59b6',
    '#1abc9c', '#e67e22', '#2ecc71', '#e91e63', '#00bcd4'
];

function openPackChart(series, parallel) {
    const overlay = document.getElementById('chart-modal-overlay');
    if (!overlay) return;
    
    overlay.classList.add('visible');
    
    // Build series selector
    buildSeriesSelector(series);
    
    // Build chart controls (toggles)
    buildChartControls();
    
    // Collect data and render chart
    setTimeout(() => {
        collectChartData(series, parallel);
        renderPackChart(parallel);
    }, 100);
}

function closePackChart() {
    const overlay = document.getElementById('chart-modal-overlay');
    if (overlay) overlay.classList.remove('visible');
    
    if (packChart) {
        packChart.destroy();
        packChart = null;
    }
}

// ==================== REPLACEMENT HISTORY ====================

function openReplacementHistory(batteryId) {
    fetch(`/replacement-history/${batteryId}/`)
        .then(r => r.json())
        .then(data => {
            showHistoryModal(data);
        })
        .catch(err => {
            console.error('Error fetching history:', err);
            toastr.error('Fehler beim Laden der Historie', 'Fehler');
        });
}

function showHistoryModal(data) {
    // Remove existing modal if any
    const existingModal = document.getElementById('history-modal-overlay');
    if (existingModal) existingModal.remove();
    
    const hasHistory = data.history && data.history.length > 0;
    
    let tableRows = '';
    if (hasHistory) {
        data.history.forEach(log => {
            const date = new Date(log.replaced_at).toLocaleString('de-CH');
            const oldCellId = extractCellId(log.old_cell_uuid);
            const newCellId = extractCellId(log.new_cell_uuid);
            tableRows += `
                <tr>
                    <td>${date}</td>
                    <td>S${log.slot_series}-P${log.slot_parallel}</td>
                    <td>${oldCellId}<br><small class="text-muted">${log.old_capacity} mAh</small></td>
                    <td>${newCellId}<br><small class="text-muted">${log.new_capacity} mAh</small></td>
                    <td>${log.reason}</td>
                </tr>
            `;
        });
    }
    
    const modalHtml = `
        <div id="history-modal-overlay" class="history-modal-overlay">
            <div class="history-modal">
                <div class="history-modal-header">
                    <h5 class="history-modal-title">
                        <i class="fa fa-history"></i> Ersetzungs-Historie: ${data.battery_name}
                    </h5>
                    <button class="history-modal-close" onclick="closeHistoryModal()">×</button>
                </div>
                <div class="history-modal-body">
                    ${hasHistory ? `
                        <table class="history-table">
                            <thead>
                                <tr>
                                    <th>Datum</th>
                                    <th>Position</th>
                                    <th>Alte Zelle</th>
                                    <th>Neue Zelle</th>
                                    <th>Grund</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${tableRows}
                            </tbody>
                        </table>
                    ` : `
                        <div class="no-history">
                            <i class="fa fa-check-circle"></i>
                            <p>Keine Ersetzungen für dieses Pack.</p>
                            <small>Alle Original-Zellen sind noch vorhanden.</small>
                        </div>
                    `}
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show with animation
    setTimeout(() => {
        document.getElementById('history-modal-overlay').classList.add('visible');
    }, 10);
    
    // Close on overlay click
    document.getElementById('history-modal-overlay').addEventListener('click', function(e) {
        if (e.target === this) closeHistoryModal();
    });
}

function closeHistoryModal() {
    const overlay = document.getElementById('history-modal-overlay');
    if (overlay) {
        overlay.classList.remove('visible');
        setTimeout(() => overlay.remove(), 300);
    }
}

// ==================== PACK PRINT & EXPORT ====================

function getPackCells() {
    const cells = [];
    const cellElements = document.querySelectorAll('.sortable-cell .list-group-item');
    
    cellElements.forEach(cell => {
        const slot = cell.closest('.sortable-cell');
        const slotId = slot ? slot.id : '';
        const slotMatch = slotId.match(/cell-(\d+)-(\d+)/);
        
        cells.push({
            cellId: extractCellId(cell.dataset.itemId),
            uuid: cell.dataset.itemId,
            capacity: parseFloat(cell.dataset.capacity) || 0,
            esr: parseFloat(cell.dataset.esr) || 0,
            voltage: parseFloat(cell.dataset.voltage) || 0,
            series: slotMatch ? parseInt(slotMatch[1]) : 0,
            parallel: slotMatch ? parseInt(slotMatch[2]) : 0
        });
    });
    
    return cells;
}

async function printPackLabels() {
    const cells = getPackCells();
    
    if (cells.length === 0) {
        toastr.error('Keine Zellen im Pack', 'Fehler');
        return;
    }
    
    toastr.info(`Drucke ${cells.length} Labels...`, 'Drucken');
    
    // Get cell database IDs for printing
    const cellIds = [];
    for (const cell of cells) {
        // We need to get the database ID from UUID
        try {
            const response = await fetch(`/get-cell-id-by-uuid/?uuid=${encodeURIComponent(cell.uuid)}`);
            const data = await response.json();
            if (data.cell_id) {
                cellIds.push(data.cell_id);
            }
        } catch (e) {
            console.error('Error getting cell ID:', e);
        }
    }
    
    if (cellIds.length === 0) {
        toastr.error('Keine druckbaren Zellen gefunden', 'Fehler');
        return;
    }
    
    // Print using existing function
    let doubleLabel = parseInt(includedValue($("#doubleLabel")));
    
    if (doubleLabel === 1) {
        for (let i = 0; i < cellIds.length; i += 2) {
            const batch = cellIds.slice(i, i + 2);
            printLabels(batch, -1);
            await sleep(1000);
        }
    } else {
        for (let i = 0; i < cellIds.length; i++) {
            printLabels([cellIds[i]], -1);
            await sleep(1000);
        }
    }
    
    toastr.success(`${cellIds.length} Labels gedruckt`, 'Fertig');
}

function exportPackCells(packName) {
    const cells = getPackCells();
    
    if (cells.length === 0) {
        toastr.error('Keine Zellen im Pack', 'Fehler');
        return;
    }
    
    // Sort by Cell-ID
    cells.sort((a, b) => a.cellId.localeCompare(b.cellId));
    
    // Sanitize pack name for filename
    const safePackName = packName.replace(/[^a-zA-Z0-9_-]/g, '_');
    
    // Create CSV content
    const headers = ['Cell-ID', 'UUID', 'Position', 'Capacity (mAh)', 'ESR (mΩ)', 'Voltage (V)'];
    const rows = cells.map(c => [
        c.cellId,
        c.uuid,
        `S${c.series}-P${c.parallel}`,
        c.capacity,
        c.esr,
        c.voltage
    ]);
    
    let csvContent = headers.join(';') + '\n';
    rows.forEach(row => {
        csvContent += row.join(';') + '\n';
    });
    
    // Add summary
    csvContent += '\n';
    csvContent += `Total Cells;${cells.length}\n`;
    csvContent += `Total Capacity;${cells.reduce((sum, c) => sum + c.capacity, 0).toFixed(0)} mAh\n`;
    csvContent += `Avg Capacity;${(cells.reduce((sum, c) => sum + c.capacity, 0) / cells.length).toFixed(1)} mAh\n`;
    csvContent += `Avg ESR;${(cells.reduce((sum, c) => sum + c.esr, 0) / cells.length).toFixed(2)} mΩ\n`;
    
    // Download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${safePackName}_cells.csv`;
    link.click();
    URL.revokeObjectURL(url);
    
    toastr.success(`${cells.length} Zellen exportiert`, 'Export');
}

function buildSeriesSelector(seriesCount) {
    const container = document.getElementById('series-selector');
    if (!container) return;
    
    totalSeriesCount = seriesCount;
    
    // Start with all series selected
    selectedSeriesSet.clear();
    for (let s = 1; s <= seriesCount; s++) {
        selectedSeriesSet.add(s);
    }
    
    let html = '<button class="series-btn active" data-series="all">Alle</button>';
    html += '<button class="series-btn" data-series="none">Keine</button>';
    for (let s = 1; s <= seriesCount; s++) {
        const color = seriesColors[(s - 1) % seriesColors.length];
        html += `<button class="series-btn active" data-series="${s}" style="--series-color: ${color}">
            <span class="series-dot" style="background:${color}"></span>S${s}
        </button>`;
    }
    container.innerHTML = html;
    
    // Event listeners
    container.querySelectorAll('.series-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const series = this.dataset.series;
            
            if (series === 'all') {
                // Select all
                selectedSeriesSet.clear();
                for (let s = 1; s <= seriesCount; s++) {
                    selectedSeriesSet.add(s);
                }
                container.querySelectorAll('.series-btn[data-series]').forEach(b => {
                    if (b.dataset.series !== 'all' && b.dataset.series !== 'none') {
                        b.classList.add('active');
                    }
                });
            } else if (series === 'none') {
                // Deselect all
                selectedSeriesSet.clear();
                container.querySelectorAll('.series-btn[data-series]').forEach(b => {
                    if (b.dataset.series !== 'all' && b.dataset.series !== 'none') {
                        b.classList.remove('active');
                    }
                });
            } else {
                // Toggle individual series
                const seriesNum = parseInt(series);
                if (selectedSeriesSet.has(seriesNum)) {
                    selectedSeriesSet.delete(seriesNum);
                    this.classList.remove('active');
                } else {
                    selectedSeriesSet.add(seriesNum);
                    this.classList.add('active');
                }
            }
            
            console.log('Selected series:', Array.from(selectedSeriesSet));
            updateChartVisibility();
        });
    });
}

function buildChartControls() {
    const container = document.getElementById('chart-controls');
    if (!container) return;
    
    let html = '';
    for (const [key, config] of Object.entries(chartColors)) {
        html += `
            <div class="chart-toggle active" style="--toggle-color: ${config.color}" data-metric="${key}">
                <span class="toggle-indicator"></span>
                <span class="toggle-label">${config.label}</span>
            </div>
        `;
    }
    container.innerHTML = html;
    
    // Event listeners - use mousedown to prevent any interference
    container.querySelectorAll('.chart-toggle').forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.toggle('active');
            console.log('Toggle metric:', this.dataset.metric, 'active:', this.classList.contains('active'));
            updateChartVisibility();
        });
    });
}

function collectChartData(seriesCount, parallelCount) {
    chartDatasets = {};
    
    for (let s = 1; s <= seriesCount; s++) {
        chartDatasets[s] = {
            capacity: [],
            esr: [],
            voltage: [],
            labels: []
        };
        
        for (let p = 1; p <= parallelCount; p++) {
            const slot = document.getElementById(`cell-${s}-${p}`);
            const cell = slot ? slot.querySelector('.list-group-item') : null;
            
            chartDatasets[s].labels.push(`P${p}`);
            
            if (cell) {
                chartDatasets[s].capacity.push(parseFloat(cell.dataset.capacity) || 0);
                chartDatasets[s].esr.push(parseFloat(cell.dataset.esr) || 0);
                chartDatasets[s].voltage.push(parseFloat(cell.dataset.voltage) || 0);
            } else {
                chartDatasets[s].capacity.push(null);
                chartDatasets[s].esr.push(null);
                chartDatasets[s].voltage.push(null);
            }
        }
    }
}

function renderPackChart(parallelCount) {
    const canvas = document.getElementById('pack-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    if (packChart) {
        packChart.destroy();
    }
    
    const labels = Array.from({ length: parallelCount }, (_, i) => `P${i + 1}`);
    const datasets = buildChartDatasets();
    
    packChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: false  // We use custom toggles
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.9)',
                    titleColor: '#4ecca3',
                    bodyColor: '#fff',
                    borderColor: '#4ecca3',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#888' }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#888' }
                },
                y1: {
                    position: 'right',
                    grid: { display: false },
                    ticks: { color: '#e74c3c' }
                }
            }
        }
    });
}

function buildChartDatasets() {
    const datasets = [];
    const activeMetrics = getActiveMetrics();
    const seriesToShow = Array.from(selectedSeriesSet).sort((a, b) => a - b);
    
    if (seriesToShow.length === 0) return datasets;
    
    const isMultiple = seriesToShow.length > 1;
    const isManySelected = seriesToShow.length > 3;
    
    seriesToShow.forEach((seriesNum) => {
        const data = chartDatasets[seriesNum];
        if (!data) return;
        
        const seriesColor = seriesColors[(seriesNum - 1) % seriesColors.length];
        const lineWidth = isManySelected ? 1.5 : 2;
        const pointRadius = isManySelected ? 0 : 3;
        
        if (activeMetrics.includes('capacity')) {
            datasets.push({
                label: `S${seriesNum} Kapazität`,
                data: data.capacity,
                borderColor: isMultiple ? seriesColor : chartColors.capacity.color,
                backgroundColor: `${isMultiple ? seriesColor : chartColors.capacity.color}33`,
                borderWidth: lineWidth,
                tension: 0.3,
                pointRadius: pointRadius,
                yAxisID: 'y',
                borderDash: [] // solid line for capacity
            });
        }
        
        if (activeMetrics.includes('esr')) {
            datasets.push({
                label: `S${seriesNum} ESR`,
                data: data.esr,
                borderColor: isMultiple ? seriesColor : chartColors.esr.color,
                backgroundColor: `${isMultiple ? seriesColor : chartColors.esr.color}33`,
                borderWidth: lineWidth,
                tension: 0.3,
                pointRadius: pointRadius,
                yAxisID: 'y1',
                borderDash: [5, 5] // dashed line for ESR
            });
        }
        
        if (activeMetrics.includes('voltage')) {
            datasets.push({
                label: `S${seriesNum} Spannung`,
                data: data.voltage,
                borderColor: isMultiple ? seriesColor : chartColors.voltage.color,
                backgroundColor: `${isMultiple ? seriesColor : chartColors.voltage.color}33`,
                borderWidth: lineWidth,
                tension: 0.3,
                pointRadius: pointRadius,
                yAxisID: 'y',
                borderDash: [2, 2] // dotted line for voltage
            });
        }
    });
    
    return datasets;
}

function getActiveMetrics() {
    const active = [];
    document.querySelectorAll('#chart-controls .chart-toggle.active').forEach(toggle => {
        active.push(toggle.dataset.metric);
    });
    return active;
}

function updateChartVisibility() {
    if (!packChart) return;
    
    const datasets = buildChartDatasets();
    packChart.data.datasets = datasets;
    packChart.update();
}

// Unsaved changes warning
window.addEventListener('beforeunload', function(e) {
    if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = 'Änderungen wurden noch nicht gespeichert. Wirklich verlassen?';
        return e.returnValue;
    }
});

// ============================================
// CHECKPOINT SYSTEM
// ============================================
const CHECKPOINT_KEY = 'megacell_assign_checkpoint';

function saveCheckpoint(series, parallel, seriesArrays, iteration, totalSwaps, scoreHistory) {
    try {
        // Convert cell elements to serializable format
        const cellPositions = seriesArrays.map(seriesArr => 
            seriesArr.map(cell => ({
                itemId: cell.dataset.itemId,
                capacity: cell.dataset.capacity,
                esr: cell.dataset.esr,
                voltage: cell.dataset.voltage
            }))
        );
        
        const checkpoint = {
            series,
            parallel,
            cellPositions,
            iteration,
            totalSwaps,
            scoreHistory,
            timestamp: Date.now()
        };
        
        localStorage.setItem(CHECKPOINT_KEY, JSON.stringify(checkpoint));
        console.log(`[Checkpoint] Saved at iteration ${iteration}`);
    } catch (e) {
        console.warn('[Checkpoint] Failed to save:', e);
    }
}

function loadCheckpoint() {
    try {
        const data = localStorage.getItem(CHECKPOINT_KEY);
        if (!data) return null;
        
        const checkpoint = JSON.parse(data);
        
        // Check if checkpoint is recent (< 1 hour old)
        const age = Date.now() - checkpoint.timestamp;
        if (age > 3600000) {
            clearCheckpoint();
            return null;
        }
        
        return checkpoint;
    } catch (e) {
        console.warn('[Checkpoint] Failed to load:', e);
        return null;
    }
}

function clearCheckpoint() {
    localStorage.removeItem(CHECKPOINT_KEY);
    console.log('[Checkpoint] Cleared');
}

function hasCheckpoint() {
    return loadCheckpoint() !== null;
}

async function resumeFromCheckpoint(checkpoint) {
    const { series, parallel, cellPositions, iteration, totalSwaps, scoreHistory } = checkpoint;
    
    updateStatus('Wiederherstellung', `Lade Checkpoint von Iteration ${iteration}...`, 10);
    await delay(300);
    
    // Get all cells from middle-list and create lookup
    const allCells = Array.from(document.querySelectorAll('#middle-list .list-group-item'));
    const cellLookup = {};
    allCells.forEach(cell => {
        cellLookup[cell.dataset.itemId] = cell;
    });
    
    // Clear all slots
    document.querySelectorAll('.sortable-cell').forEach(slot => {
        slot.innerHTML = '';
        slot.classList.remove('cell-placing', 'cell-placed', 'cell-done');
    });
    
    // Restore cell positions
    let seriesArrays = [];
    for (let s = 0; s < series; s++) {
        seriesArrays[s] = [];
        for (let p = 0; p < parallel; p++) {
            const cellData = cellPositions[s][p];
            const cell = cellLookup[cellData.itemId];
            
            if (cell) {
                seriesArrays[s].push(cell);
                const slot = getSlot(s, p);
                placeCellInSlot(cell, slot, false);
                slot.classList.add('cell-placed');
            }
            
            // Update progress
            const progress = 10 + ((s * parallel + p) / (series * parallel)) * 30;
            updateStatus('Wiederherstellung', `Stelle Zellen wieder her... (S${s+1}P${p+1})`, progress);
        }
    }
    
    updateStatus('Wiederherstellung', `Checkpoint geladen. Setze bei Iteration ${iteration} fort...`, 45);
    await delay(500);
    
    // Continue with remaining iterations
    const maxIterations = 100;
    const earlyStopThreshold = 0.005;
    let improved = true;
    let currentIteration = iteration;
    let currentTotalSwaps = totalSwaps;
    let previousScore = scoreHistory[scoreHistory.length - 1]?.score || calculateBalancingScore(seriesArrays);
    let initialScore = scoreHistory[0]?.score || previousScore;
    
    console.log(`[Resume] Continuing from iteration ${currentIteration}, score ${previousScore.toFixed(4)}`);
    
    while (improved && currentIteration < maxIterations) {
        improved = false;
        currentIteration++;
        
        let currentScore = calculateBalancingScore(seriesArrays);
        let iterationSwaps = 0;

        for (let a = 0; a < series; a++) {
            for (let b = a + 1; b < series; b++) {
                for (let i = 0; i < seriesArrays[a].length; i++) {
                    for (let j = 0; j < seriesArrays[b].length; j++) {
                        let temp = seriesArrays[a][i];
                        seriesArrays[a][i] = seriesArrays[b][j];
                        seriesArrays[b][j] = temp;

                        let newScore = calculateBalancingScore(seriesArrays);

                        if (newScore < currentScore) {
                            currentScore = newScore;
                            improved = true;
                            currentTotalSwaps++;
                            iterationSwaps++;
                            
                            if (currentTotalSwaps % 5 === 0) {
                                const slotA = getSlot(a, i);
                                const slotB = getSlot(b, j);
                                await animateSwap(slotA, slotB);
                                
                                const cellA = slotA.firstChild;
                                const cellB = slotB.firstChild;
                                if (cellA && cellB) {
                                    slotA.innerHTML = '';
                                    slotB.innerHTML = '';
                                    slotA.appendChild(cellB);
                                    slotB.appendChild(cellA);
                                }
                            }
                        } else {
                            seriesArrays[b][j] = seriesArrays[a][i];
                            seriesArrays[a][i] = temp;
                        }
                    }
                }
            }
        }
        
        const improvement = previousScore > 0 ? ((previousScore - currentScore) / previousScore) * 100 : 0;
        console.log(`[Score] Iter ${currentIteration}: ${currentScore.toFixed(4)} (-${improvement.toFixed(2)}%)`);
        
        if (improved && improvement < earlyStopThreshold && currentIteration > iteration + 5) {
            console.log(`[Score] Early stop after resume`);
            break;
        }
        
        previousScore = currentScore;
        
        if (currentIteration % 10 === 0) {
            saveCheckpoint(series, parallel, seriesArrays, currentIteration, currentTotalSwaps, scoreHistory);
        }
        
        const progress = 46 + ((currentIteration - iteration) / (maxIterations - iteration)) * 45;
        const scoreReduction = ((initialScore - currentScore) / initialScore * 100).toFixed(1);
        updateStatus('Phase 2 (fortgesetzt)', `Iter ${currentIteration} | ${currentTotalSwaps} Swaps | -${scoreReduction}%`, progress);
        
        if (currentIteration % 2 === 0) await delay(15);
    }
    
    clearCheckpoint();
    
    // Finalize
    updateStatus('Finalisierung', 'Berechne Statistiken...', 92);
    await delay(100);

    for (let s = 0; s < series; s++) {
        for (let p = 0; p < parallel; p++) {
            const slot = getSlot(s, p);
            const cell = seriesArrays[s][p];
            if (slot && cell && slot.firstChild !== cell) {
                placeCellInSlot(cell, slot, false);
            }
        }
    }

    const finalCapacities = seriesArrays.map(s => calculateGroupCapacity(s));
    const capStdDev = calculateStdDev(finalCapacities);
    
    console.log('Resume complete:', currentIteration, 'total iterations,', currentTotalSwaps, 'total swaps');

    markAllCellsDone();
    setupCellTooltips();
    updateAllCapacities();

    hideStatus();
    
    // Show result banner
    showResultBanner({
        cells: series * parallel,
        iterations: currentIteration,
        swaps: currentTotalSwaps,
        stdDev: capStdDev.toFixed(1)
    });
}

// Get slot element by series and parallel index
function getSlot(s, p) {
    return document.getElementById(`cell-${s + 1}-${p + 1}`);
}

// Place cell in slot with animation
function placeCellInSlot(cell, slot, animate = true) {
    if (!slot || !cell) return;
    
    // Extract Cell-ID for display
    const cellId = extractCellId(cell.dataset.itemId || '');
    
    // Update cell display to show just the ID (no title - we use custom tooltip)
    cell.textContent = cellId;
    
    slot.innerHTML = '';
    slot.appendChild(cell);
    
    if (animate) {
        slot.classList.add('cell-placing');
        setTimeout(() => {
            slot.classList.remove('cell-placing');
            slot.classList.add('cell-placed');
        }, 150);
    }
}

// Animate swap between two slots
async function animateSwap(slotA, slotB) {
    slotA.classList.add('cell-swap-source');
    slotB.classList.add('cell-swap-target');
    
    await delay(80);
    
    slotA.classList.remove('cell-swap-source');
    slotB.classList.remove('cell-swap-target');
}

// Mark all cells as done (green)
function markAllCellsDone() {
    document.querySelectorAll('.sortable-cell').forEach(slot => {
        slot.classList.remove('cell-placing', 'cell-placed', 'cell-swap-source', 'cell-swap-target');
        if (slot.children.length > 0) {
            slot.classList.add('cell-done');
        }
    });
}

// Setup hover tooltips for cells
function setupCellTooltips() {
    const tooltip = document.createElement('div');
    tooltip.className = 'cell-tooltip';
    tooltip.style.display = 'none';
    document.body.appendChild(tooltip);
    
    document.querySelectorAll('.sortable-cell .list-group-item').forEach(cell => {
        cell.addEventListener('mouseenter', function(e) {
            const cap = this.dataset.capacity || '?';
            const esr = this.dataset.esr || '?';
            const volt = this.dataset.voltage || '?';
            const id = this.dataset.itemId || '?';
            
            tooltip.innerHTML = `
                <div class="tooltip-row"><span class="tooltip-label">ID:</span><span class="tooltip-value">${id}</span></div>
                <div class="tooltip-row"><span class="tooltip-label">Kapazität:</span><span class="tooltip-value">${cap} mAh</span></div>
                <div class="tooltip-row"><span class="tooltip-label">ESR:</span><span class="tooltip-value">${esr} mΩ</span></div>
                <div class="tooltip-row"><span class="tooltip-label">Spannung:</span><span class="tooltip-value">${volt} V</span></div>
            `;
            tooltip.style.display = 'block';
        });
        
        cell.addEventListener('mousemove', function(e) {
            tooltip.style.left = (e.pageX + 15) + 'px';
            tooltip.style.top = (e.pageY + 10) + 'px';
        });
        
        cell.addEventListener('mouseleave', function() {
            tooltip.style.display = 'none';
        });
    });
}

// Assign Cells to pack with Visual Animation
async function assignCellsToPack(series, parallel) {
    // Check for existing checkpoint
    const checkpoint = loadCheckpoint();
    if (checkpoint && checkpoint.series === series && checkpoint.parallel === parallel) {
        const age = Math.round((Date.now() - checkpoint.timestamp) / 60000);
        const resume = confirm(
            `Checkpoint gefunden!\n\n` +
            `Iteration: ${checkpoint.iteration}\n` +
            `Swaps: ${checkpoint.totalSwaps}\n` +
            `Alter: ${age} Minuten\n\n` +
            `Fortsetzen?`
        );
        
        if (resume) {
            await resumeFromCheckpoint(checkpoint);
            return;
        } else {
            clearCheckpoint();
        }
    }
    
    const cells = Array.from(document.querySelectorAll('#middle-list .list-group-item'));
    const requiredCells = series * parallel;

    updateStatus('Vorbereitung', `Prüfe Zellen... (${cells.length} verfügbar)`, 2);
    await delay(200);

    if (cells.length < requiredCells) {
        hideStatus();
        toastr.warning(`Nicht genug Zellen. Benötigt: ${requiredCells}, Verfügbar: ${cells.length}`, "Warnung");
        return;
    }

    updateStatus('Vorbereitung', `Sortiere ${cells.length} Zellen nach Kapazität...`, 5);
    await delay(150);

    // Sort by capacity descending
    cells.sort((a, b) => parseFloat(b.dataset.capacity) - parseFloat(a.dataset.capacity));

    // Clear all slots first
    document.querySelectorAll('.sortable-cell').forEach(slot => {
        slot.innerHTML = '';
        slot.classList.remove('cell-placing', 'cell-placed', 'cell-done', 'cell-swap-source', 'cell-swap-target');
    });

    // ============================================
    // PHASE 1: Serpentine Distribution with Animation
    // ============================================
    updateStatus('Phase 1', 'Serpentine-Verteilung startet...', 8);
    await delay(100);

    let seriesArrays = Array.from({ length: series }, () => []);
    let cellIndex = 0;
    const animationDelay = Math.max(5, Math.min(50, 2000 / requiredCells)); // Adaptive speed

    for (let p = 0; p < parallel; p++) {
        const forward = (p % 2 === 0);
        
        for (let step = 0; step < series && cellIndex < cells.length; step++) {
            const s = forward ? step : (series - 1 - step);
            const cell = cells[cellIndex];
            const slot = getSlot(s, p);
            
            seriesArrays[s].push(cell);
            placeCellInSlot(cell, slot, true);
            
            cellIndex++;
            
            // Update progress
            const progress = 8 + (cellIndex / requiredCells) * 35;
            updateStatus('Phase 1', `Serpentine-Verteilung (${cellIndex}/${requiredCells})`, progress);
            
            await delay(animationDelay);
        }
    }

    updateStatus('Phase 1', 'Verteilung abgeschlossen!', 45);
    await delay(300);

    // ============================================
    // PHASE 2: Multi-Objective Swap Balancing with Score Tracking
    // ============================================
    updateStatus('Phase 2', 'Swap-Balancing startet...', 46);
    await delay(200);

    const maxIterations = 100;
    const earlyStopThreshold = 0.005; // Stop if improvement < 0.5%
    let improved = true;
    let iteration = 0;
    let totalSwaps = 0;
    let visualSwaps = 0;
    
    // Score tracking
    let scoreHistory = [];
    let initialScore = calculateBalancingScore(seriesArrays);
    let previousScore = initialScore;
    scoreHistory.push({ iteration: 0, score: initialScore, improvement: 0 });
    
    console.log(`[Score] Initial: ${initialScore.toFixed(4)}`);

    while (improved && iteration < maxIterations) {
        improved = false;
        iteration++;
        
        let currentScore = calculateBalancingScore(seriesArrays);
        let iterationSwaps = 0;

        for (let a = 0; a < series; a++) {
            for (let b = a + 1; b < series; b++) {
                for (let i = 0; i < seriesArrays[a].length; i++) {
                    for (let j = 0; j < seriesArrays[b].length; j++) {
                        // Try swap
                        let temp = seriesArrays[a][i];
                        seriesArrays[a][i] = seriesArrays[b][j];
                        seriesArrays[b][j] = temp;

                        let newScore = calculateBalancingScore(seriesArrays);

                        if (newScore < currentScore) {
                            currentScore = newScore;
                            improved = true;
                            totalSwaps++;
                            iterationSwaps++;
                            
                            // Visual swap in DOM (every Nth swap for performance)
                            if (totalSwaps % 5 === 0 || totalSwaps < 10) {
                                const slotA = getSlot(a, i);
                                const slotB = getSlot(b, j);
                                
                                await animateSwap(slotA, slotB);
                                
                                const cellA = slotA.firstChild;
                                const cellB = slotB.firstChild;
                                if (cellA && cellB) {
                                    slotA.innerHTML = '';
                                    slotB.innerHTML = '';
                                    slotA.appendChild(cellB);
                                    slotB.appendChild(cellA);
                                }
                                
                                visualSwaps++;
                            }
                        } else {
                            // Revert swap
                            seriesArrays[b][j] = seriesArrays[a][i];
                            seriesArrays[a][i] = temp;
                        }
                    }
                }
            }
        }
        
        // Track score improvement
        const improvement = previousScore > 0 ? ((previousScore - currentScore) / previousScore) * 100 : 0;
        scoreHistory.push({ iteration, score: currentScore, improvement, swaps: iterationSwaps });
        
        console.log(`[Score] Iter ${iteration}: ${currentScore.toFixed(4)} (${improvement > 0 ? '-' : '+'}${Math.abs(improvement).toFixed(2)}%, ${iterationSwaps} swaps)`);
        
        // Early stop if improvement is negligible
        if (improved && improvement < earlyStopThreshold && iteration > 5) {
            console.log(`[Score] Early stop: Improvement ${improvement.toFixed(3)}% < ${earlyStopThreshold}%`);
            break;
        }
        
        previousScore = currentScore;
        
        // Save checkpoint every 10 iterations
        if (iteration % 10 === 0) {
            saveCheckpoint(series, parallel, seriesArrays, iteration, totalSwaps, scoreHistory);
        }
        
        // Update status with score info
        const progress = 46 + (iteration / maxIterations) * 45;
        const scoreReduction = ((initialScore - currentScore) / initialScore * 100).toFixed(1);
        updateStatus('Phase 2', `Iter ${iteration} | ${totalSwaps} Swaps | Score -${scoreReduction}%`, progress);
        
        // Allow UI to breathe
        if (iteration % 2 === 0) await delay(15);
    }
    
    // Clear checkpoint on successful completion
    clearCheckpoint();

    // ============================================
    // PHASE 3: Finalize
    // ============================================
    updateStatus('Finalisierung', 'Berechne Statistiken...', 92);
    await delay(100);

    // Ensure final state is in DOM
    for (let s = 0; s < series; s++) {
        for (let p = 0; p < parallel; p++) {
            const slot = getSlot(s, p);
            const cell = seriesArrays[s][p];
            if (slot && cell && slot.firstChild !== cell) {
                placeCellInSlot(cell, slot, false);
            }
        }
    }

    // Calculate final stats
    const finalCapacities = seriesArrays.map(s => calculateGroupCapacity(s));
    const finalResistances = seriesArrays.map(s => calculateGroupResistance(s));
    const capStdDev = calculateStdDev(finalCapacities);
    const resStdDev = calculateStdDev(finalResistances);
    
    console.log('Balancing complete:', iteration, 'iterations,', totalSwaps, 'swaps');
    console.log('Capacity StdDev:', capStdDev.toFixed(2), 'mAh');
    console.log('Resistance StdDev:', resStdDev.toFixed(4), 'mΩ');

    updateStatus('Finalisierung', 'Markiere Zellen...', 96);
    await delay(100);

    // Mark all cells as done (green)
    markAllCellsDone();
    
    // Setup hover tooltips
    setupCellTooltips();
    
    updateAllCapacities();

    // Hide status and show result banner
    hideStatus();
    
    // Show result banner with stats
    showResultBanner({
        cells: requiredCells,
        iterations: iteration,
        swaps: totalSwaps,
        stdDev: capStdDev.toFixed(1)
    });
}



function updateUIAfterAssignment() {
    // Example UI update
    document.getElementById('assign-btn').disabled = true; // Disable button after assignment
}

// Find best replacement cell for a defective cell in the pack
function findReplacementCell(defectiveCellElement) {
    const reservePool = Array.from(document.querySelectorAll('#left-list .list-group-item'));
    
    if (reservePool.length === 0) {
        toastr.error('Keine Ersatzzellen im Reserve-Pool verfügbar', 'Fehler');
        return null;
    }

    const defectiveCapacity = parseFloat(defectiveCellElement.dataset.capacity);
    const defectiveEsr = parseFloat(defectiveCellElement.dataset.esr) || 0;

    // Find best match: minimize combined delta of capacity and ESR
    let bestMatch = null;
    let bestScore = Infinity;

    reservePool.forEach(cell => {
        const cellCapacity = parseFloat(cell.dataset.capacity);
        const cellEsr = parseFloat(cell.dataset.esr) || 0;

        // Calculate normalized deltas
        const deltaCap = Math.abs(cellCapacity - defectiveCapacity) / 100; // Normalize
        const deltaEsr = Math.abs(cellEsr - defectiveEsr) * 10; // Normalize

        // Weighted score (capacity more important)
        const score = (0.6 * deltaCap) + (0.4 * deltaEsr);

        if (score < bestScore) {
            bestScore = score;
            bestMatch = cell;
        }
    });

    if (bestMatch) {
        console.log('Best replacement found:', {
            uuid: bestMatch.dataset.itemId,
            capacity: bestMatch.dataset.capacity,
            esr: bestMatch.dataset.esr,
            score: bestScore.toFixed(4)
        });
    }

    return bestMatch;
}

// Replace a defective cell in a slot with the best match from reserve
function replaceDefectiveCell(slotId) {
    const slot = document.getElementById(slotId);
    if (!slot) {
        toastr.error('Slot nicht gefunden', 'Fehler');
        return;
    }

    const defectiveCell = slot.querySelector('.list-group-item');
    if (!defectiveCell) {
        toastr.error('Keine Zelle in diesem Slot', 'Fehler');
        return;
    }

    const replacement = findReplacementCell(defectiveCell);
    if (replacement) {
        // Parse slot position from ID (format: cell-S-P)
        const slotMatch = slotId.match(/cell-(\d+)-(\d+)/);
        const slotSeries = slotMatch ? parseInt(slotMatch[1]) : 0;
        const slotParallel = slotMatch ? parseInt(slotMatch[2]) : 0;
        
        // Extract Cell-IDs for display
        const oldCellId = extractCellId(defectiveCell.dataset.itemId);
        const newCellId = extractCellId(replacement.dataset.itemId);
        
        // Log replacement to server
        if (currentBatteryId) {
            fetch('/log-cell-replacement/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    battery_id: currentBatteryId,
                    old_cell_uuid: defectiveCell.dataset.itemId,
                    new_cell_uuid: replacement.dataset.itemId,
                    slot_series: slotSeries,
                    slot_parallel: slotParallel,
                    old_capacity: parseFloat(defectiveCell.dataset.capacity),
                    new_capacity: parseFloat(replacement.dataset.capacity),
                    old_esr: parseFloat(defectiveCell.dataset.esr) || null,
                    new_esr: parseFloat(replacement.dataset.esr) || null,
                    reason: 'defective'
                })
            }).then(r => r.json()).then(data => {
                if (data.success) {
                    console.log('Replacement logged:', data.message);
                }
            }).catch(err => console.error('Log failed:', err));
        }
        
        // Move defective cell to middle-list (or mark as defective)
        const middleList = document.getElementById('middle-list');
        defectiveCell.classList.add('defective');
        defectiveCell.style.backgroundColor = '#ffcccc';
        middleList.appendChild(defectiveCell);

        // Move replacement to slot and highlight
        slot.appendChild(replacement);
        slot.classList.add('cell-replaced');
        replacement.classList.add('replacement-highlight');
        
        // Remove highlight after animation
        setTimeout(() => {
            slot.classList.remove('cell-replaced');
            replacement.classList.remove('replacement-highlight');
        }, 3000);

        // Clear, detailed success message
        toastr.success(
            `<div style="line-height: 1.6">
                <strong>Position:</strong> S${slotSeries}-P${slotParallel}<br>
                <strong>Alte Zelle:</strong> ${oldCellId} (${defectiveCell.dataset.capacity} mAh)<br>
                <strong>Neue Zelle:</strong> ${newCellId} (${replacement.dataset.capacity} mAh)
            </div>`,
            '✓ Zelle erfolgreich ersetzt',
            { timeOut: 8000, escapeHtml: false }
        );

        updateAllCapacities();
    }
}

// ==================== CONTEXT MENU ====================

let contextMenuTarget = null;
let contextMenuSlot = null;

function setupCellContextMenu() {
    const contextMenu = document.getElementById('cell-context-menu');
    if (!contextMenu) return;

    // Right-click on cells in battery layout
    document.addEventListener('contextmenu', function(e) {
        const cell = e.target.closest('.sortable-cell .list-group-item');
        const slot = e.target.closest('.sortable-cell');
        
        if (cell && slot) {
            e.preventDefault();
            contextMenuTarget = cell;
            contextMenuSlot = slot;
            
            // Position menu
            contextMenu.style.left = e.clientX + 'px';
            contextMenu.style.top = e.clientY + 'px';
            contextMenu.classList.add('show');
        } else {
            hideContextMenu();
        }
    });

    // Hide on click outside
    document.addEventListener('click', function(e) {
        if (!contextMenu.contains(e.target)) {
            hideContextMenu();
        }
    });

    // Hide on scroll
    document.addEventListener('scroll', hideContextMenu, true);

    // Replace cell action
    document.getElementById('ctx-replace-cell').addEventListener('click', function() {
        if (contextMenuSlot) {
            replaceDefectiveCell(contextMenuSlot.id);
        }
        hideContextMenu();
    });

    // Show details action
    document.getElementById('ctx-show-details').addEventListener('click', function() {
        if (contextMenuTarget) {
            const uuid = contextMenuTarget.dataset.itemId;
            const cap = contextMenuTarget.dataset.capacity;
            const esr = contextMenuTarget.dataset.esr || 'N/A';
            const voltage = contextMenuTarget.dataset.voltage || 'N/A';
            
            toastr.info(
                `UUID: ${uuid}<br>Kapazität: ${cap} mAh<br>ESR: ${esr} mΩ<br>Spannung: ${voltage} V`,
                'Zell-Details',
                { timeOut: 10000, escapeHtml: false }
            );
        }
        hideContextMenu();
    });

    // Remove cell action
    document.getElementById('ctx-remove-cell').addEventListener('click', function() {
        if (contextMenuTarget && contextMenuSlot) {
            const middleList = document.getElementById('middle-list');
            middleList.appendChild(contextMenuTarget);
            updateAllCapacities();
            toastr.success('Zelle zurück in Transfer-Liste verschoben', 'Entfernt');
        }
        hideContextMenu();
    });
}

function hideContextMenu() {
    const contextMenu = document.getElementById('cell-context-menu');
    if (contextMenu) {
        contextMenu.classList.remove('show');
    }
    contextMenuTarget = null;
    contextMenuSlot = null;
}

// Initialize context menu when DOM is ready
document.addEventListener('DOMContentLoaded', setupCellContextMenu);



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
function showDeleteConfirmation(batteryId) {
    // Set the deviceId to a data attribute on the confirm button for later use
    document.getElementById('confirmDeleteBtn').setAttribute('data-battery-id', batteryId);

    // Show the modal using Bootstrap's modal method
    var deleteConfirmationModal = new bootstrap.Modal(document.getElementById('deleteConfirmationModal'), {
        keyboard: false
    });
    deleteConfirmationModal.show();
}

// Add event listeners to delete buttons
document.querySelectorAll('.deleteBatteryBtn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();  // Prevent the default link behavior
        const batteryId = this.getAttribute('data-battery-id');

        showDeleteConfirmation(batteryId);  // Show confirmation modal
    });
});

// Add event listener to the confirmation button in the modal
document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
    const batteryId = this.getAttribute('data-battery-id');
    console.log(batteryId);
    deleteBattery(batteryId);  // Proceed to delete the battery pack
    $('#deleteConfirmationModal').modal('hide');  // Hide the confirmation modal
});

    // Delete battery pack function
function deleteBattery(batteryId) {
    fetch("/delete-batteries/", {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'battery_ids': [batteryId] })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        toastr.success('Battery-Pack gelöscht', 'Erfolg');
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        toastr.error('Fehler beim Löschen', 'Fehler');
    });
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



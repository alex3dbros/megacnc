let capacityUpdateInterval;

function sleep(ms) {
    return new Promise(function (resolve) {
        setTimeout(resolve, ms);
    });
}

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

function fetchCells(projectId, packBatteryId) {
    const data = { project_id: projectId };
    if (packBatteryId) {
        data.for_pack_battery_id = packBatteryId;
    }
    $.ajax({
        url: '/get-cells',
        type: 'GET',
        data: data,
        success: function (response) {
            updateCellsList(response.cells);
        },
        error: function () {
            toastr.error('Could not load cells for this project.', 'Error');
        }
    });
}

function updateCellsList(cells) {
    const cellsList = $('#left-list');
    cellsList.empty();
    cells.forEach(function (cell) {
        var listItem = document.createElement('div');
        listItem.className = 'list-group-item';
        listItem.textContent = cell.id + ' — ' + cell.capacity + ' mAh (ESR ' + (cell.esr != null ? cell.esr : '—') + ')';
        listItem.dataset.itemId = String(cell.uuid);
        listItem.dataset.capacity = String(cell.capacity);
        listItem.dataset.esr = cell.esr != null ? String(cell.esr) : '0';
        cellsList.append(listItem);
    });
}

/** QR / etichetă: D20240219-S000001-C3245-mAh → prefix D20240219-S000001 */
function parseQrToCellUuidPrefix(raw) {
    var t = (raw || '').trim();
    if (!t) return '';
    var m = t.match(/^(D\d{8}-S\d+)/i);
    if (m) return m[1];
    var idx = t.indexOf('-C');
    if (idx !== -1) return t.slice(0, idx);
    return t.split('-mAh')[0].trim();
}

function findListItemByUuidPrefix(uuidPrefix) {
    var found = null;
    document.querySelectorAll('.list-group-item').forEach(function (li) {
        if (!li.dataset.itemId) return;
        if (li.dataset.itemId === uuidPrefix) {
            found = li;
        }
    });
    if (found) return found;
    document.querySelectorAll('.list-group-item').forEach(function (li) {
        if (!li.dataset.itemId) return;
        if (li.dataset.itemId.indexOf(uuidPrefix) === 0) {
            found = li;
        }
    });
    return found;
}

/** Alege string-ul (rândul) unde, după plasarea acestei celule, suma cap+ESR e cea mai mică (echilibrare). */
function pickTargetStringIndex(cellEl, series, parallel) {
    var cap = parseFloat(cellEl.dataset.capacity || '0');
    var esr = parseFloat(cellEl.dataset.esr || '0');
    var bestS = 1;
    var bestScore = Infinity;
    var found = false;
    for (var s = 1; s <= series; s++) {
        var sc = 0;
        var se = 0;
        var cnt = 0;
        for (var j = 0; j < parallel; j++) {
            var slot = document.getElementById('cell-' + s + String.fromCharCode(65 + j));
            if (!slot) continue;
            slot.querySelectorAll('.list-group-item').forEach(function (li) {
                sc += parseFloat(li.dataset.capacity || '0');
                se += parseFloat(li.dataset.esr || '0');
                cnt++;
            });
        }
        if (cnt >= parallel) continue;
        var projectedCap = sc + cap;
        var projectedEsr = se + esr;
        var score = projectedCap + 0.0001 * projectedEsr;
        if (score < bestScore) {
            bestScore = score;
            bestS = s;
        }
        found = true;
    }
    return found ? bestS : null;
}

function clearStringHighlights() {
    document.querySelectorAll('tr.mcc-string-highlight').forEach(function (tr) {
        tr.classList.remove('mcc-string-highlight');
    });
}

function highlightStringRow(stringIndex) {
    clearStringHighlights();
    var tr = document.querySelector('#battery-pack-container tr[data-string-index="' + stringIndex + '"]');
    if (tr) {
        tr.classList.add('mcc-string-highlight');
        tr.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
    window.setTimeout(clearStringHighlights, 3500);
}

function moveCellToFirstFreeSlotInString(cellEl, stringIndex, parallel) {
    for (var j = 0; j < parallel; j++) {
        var slot = document.getElementById('cell-' + stringIndex + String.fromCharCode(65 + j));
        if (!slot) continue;
        if (slot.querySelectorAll('.list-group-item').length === 0) {
            slot.appendChild(cellEl);
            return true;
        }
    }
    return false;
}

function collectPackCellsData() {
    var cellsData = [];
    document.querySelectorAll('.sortable-cell').forEach(function (slot) {
        slot.querySelectorAll('.list-group-item').forEach(function (cell) {
            cellsData.push({
                cellId: cell.dataset.itemId,
                slotId: slot.id,
                capacity: cell.dataset.capacity
            });
        });
    });
    return cellsData;
}

function getSelectedPackProjectId() {
    var btn = document.getElementById('pack-project-dropdown-btn');
    if (!btn || !btn.dataset.selectedProjectId) return null;
    return btn.dataset.selectedProjectId;
}

function createProjectDropdown(projects, packBatteryId, initialProjectId, initialProjectName) {
    var dropdownDiv = document.createElement('div');
    dropdownDiv.className = 'dropdown mb-2';

    var button = document.createElement('button');
    button.className = 'btn btn-outline-secondary btn-sm dropdown-toggle';
    button.setAttribute('type', 'button');
    button.setAttribute('data-bs-toggle', 'dropdown');
    button.id = 'pack-project-dropdown-btn';
    button.dataset.selectedProjectId = initialProjectId != null ? String(initialProjectId) : '';
    button.textContent = initialProjectName || 'Selectează proiect';

    var dropdownMenu = document.createElement('div');
    dropdownMenu.className = 'dropdown-menu';

    projects.forEach(function (project) {
        var option = document.createElement('a');
        option.className = 'dropdown-item';
        option.href = 'javascript:void(0);';
        option.textContent = project.name;
        option.onclick = function () {
            button.textContent = project.name;
            button.dataset.selectedProjectId = String(project.id);
            fetchCells(String(project.id), packBatteryId);
        };
        dropdownMenu.appendChild(option);
    });

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
    var toIdx = event.to && event.to.dataset && event.to.dataset.series;
    var fromIdx = event.from && event.from.dataset && event.from.dataset.series;
    if (toIdx) {
        updateSeriesCapacityById(toIdx);
    }
    if (fromIdx && fromIdx !== toIdx) {
        updateSeriesCapacityById(fromIdx);
    }
}


function populateSlotsFromPackMeta(cells) {
    (cells || []).forEach(function (cell) {
        var slot = document.getElementById(cell.bat_position);
        if (!slot) return;
        var listItem = document.createElement('li');
        listItem.textContent = cell.id + ' — ' + cell.capacity + ' mAh';
        listItem.className = 'list-group-item';
        listItem.dataset.itemId = cell.uuid;
        listItem.dataset.capacity = String(cell.capacity);
        listItem.dataset.esr = cell.esr != null ? String(cell.esr) : '0';
        slot.appendChild(listItem);
    });
    if (typeof updateAllCapacities === 'function') {
        updateAllCapacities();
    }
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
    if (transferCellsTitle) {
        transferCellsTitle.textContent = 'Staging (' + middleListCellsCount + ')';
    }
}


function updateSeriesCapacityById(seriesId) {
    const cells = document.querySelectorAll(`[data-series="${seriesId}"] .list-group-item`);
    let totalCapacity = 0;
    let totalEsr = 0;

    cells.forEach(cell => {
        totalCapacity += parseFloat(cell.dataset.capacity || 0);
        totalEsr += parseFloat(cell.dataset.esr || 0);
    });

    const capacityDisplay = document.getElementById(`capacity-${seriesId}`);
    if (capacityDisplay) {
        capacityDisplay.textContent = `${totalCapacity.toFixed(2)} mAh`;
    }
    const esrDisplay = document.getElementById(`esrsum-${seriesId}`);
    if (esrDisplay) {
        esrDisplay.textContent = totalEsr.toFixed(4);
    }
}


function createBatteryLayout(series, parallel) {
    const container = document.createElement('div');
    container.className = 'col-12';
    const title = document.createElement('h5');
    title.className = 'text-center mb-2 text-muted';
    title.textContent = 'Pack grid';
    container.appendChild(title);
    const subtitle = document.createElement('p');
    subtitle.className = 'small text-muted text-center mb-2';
    subtitle.textContent = 'Each row = one string (all cells in parallel on that branch). Rows are in series. Columns = parallel positions P1…P' + parallel + '.';
    container.appendChild(subtitle);

    const table = document.createElement('table');
    table.className = 'table table-sm table-bordered align-middle mcc-pack-grid';

    const thead = document.createElement('thead');
    thead.className = 'table-light';
    const headerRow = document.createElement('tr');
    const thCorner = document.createElement('th');
    thCorner.scope = 'col';
    thCorner.className = 'text-center mcc-pack-sticky-col';
    thCorner.textContent = '#';
    thCorner.title = 'String index: one parallel group per row; strings in series';
    headerRow.appendChild(thCorner);
    for (let j = 0; j < parallel; j++) {
        const th = document.createElement('th');
        th.scope = 'col';
        th.className = 'text-center';
        th.textContent = 'P' + (j + 1);
        th.title = 'Parallel position ' + (j + 1) + ' within this string';
        headerRow.appendChild(th);
    }
    const thCap = document.createElement('th');
    thCap.scope = 'col';
    thCap.className = 'text-center';
    thCap.textContent = 'Σ mAh';
    thCap.title = 'Total capacity in this string (parallel group)';
    headerRow.appendChild(thCap);
    const thEsr = document.createElement('th');
    thEsr.scope = 'col';
    thEsr.className = 'text-center';
    thEsr.textContent = 'Σ ESR';
    thEsr.title = 'Total ESR in this string';
    headerRow.appendChild(thEsr);
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    for (let i = 0; i < series; i++) {
        const tr = document.createElement('tr');
        tr.dataset.stringIndex = String(i + 1);
        const rowNumberCell = document.createElement('td');
        rowNumberCell.textContent = 'S' + (i + 1);
        rowNumberCell.className = 'text-center fw-bold text-nowrap mcc-pack-sticky-col';
        rowNumberCell.title = 'String ' + (i + 1) + ' (parallel group)';
        tr.appendChild(rowNumberCell);

        for (let j = 0; j < parallel; j++) {
            const td = document.createElement('td');
            const cellList = document.createElement('ul');
            cellList.className = 'sortable-cell';
            cellList.id = `cell-${i + 1}${String.fromCharCode(65 + j)}`;
            cellList.dataset.series = i + 1;

            td.appendChild(cellList);
            tr.appendChild(td);
        }

        const capacityCell = document.createElement('td');
        capacityCell.className = 'text-center capacity-display';
        capacityCell.id = `capacity-${i + 1}`;
        capacityCell.textContent = '0 mAh';
        tr.appendChild(capacityCell);

        const esrCell = document.createElement('td');
        esrCell.className = 'text-center esrsum-display';
        esrCell.id = `esrsum-${i + 1}`;
        esrCell.textContent = '0';
        tr.appendChild(esrCell);

        tbody.appendChild(tr);
    }

    table.appendChild(tbody);

    const scrollWrap = document.createElement('div');
    scrollWrap.className = 'mcc-pack-grid-scroll';
    const totalSlots = series * parallel;
    if (parallel > 8 || series > 10 || totalSlots > 56) {
        scrollWrap.classList.add('mcc-pack-grid--dense');
    }
    scrollWrap.appendChild(table);
    container.appendChild(scrollWrap);

    return container;
}

/**
 * Exportă planul curent de plasare / echilibrare ca CSV (separator ; pentru Excel RO).
 */
function exportPackPlanCsv(batteryId, series, parallel) {
    const sep = ';';
    const lines = [];

    lines.push('# Mega CNC — plan de echilibrare pack');
    lines.push('# string = parallel group per row; slot_id cell-1A = string 1, parallel pos. A (internal id; UI shows P1…Pn)');
    lines.push(['battery_id', String(batteryId)].join(sep));
    lines.push(['strings_S', String(series), 'parallel_P', String(parallel)].join(sep));
    lines.push(['exported_at', new Date().toISOString()].join(sep));
    lines.push('');
    lines.push(['string_label', 'slot_id', 'cell_uuid', 'capacity_mAh', 'esr'].join(sep));

    for (let s = 1; s <= series; s++) {
        for (let j = 0; j < parallel; j++) {
            const slotId = 'cell-' + s + String.fromCharCode(65 + j);
            const slot = document.getElementById(slotId);
            if (!slot) continue;
            slot.querySelectorAll('.list-group-item').forEach(function (li) {
                lines.push([
                    'String ' + s,
                    slotId,
                    (li.dataset.itemId || '').replace(/"/g, '""'),
                    li.dataset.capacity || '',
                    li.dataset.esr != null ? li.dataset.esr : ''
                ].join(sep));
            });
        }
    }

    lines.push('');
    lines.push(['string_label', 'sum_capacity_mAh', 'sum_esr', 'cells_in_string'].join(sep));
    for (let s = 1; s <= series; s++) {
        let sc = 0;
        let se = 0;
        let cnt = 0;
        for (let j = 0; j < parallel; j++) {
            const slot = document.getElementById('cell-' + s + String.fromCharCode(65 + j));
            if (!slot) continue;
            slot.querySelectorAll('.list-group-item').forEach(function (li) {
                sc += parseFloat(li.dataset.capacity || 0);
                se += parseFloat(li.dataset.esr || 0);
                cnt++;
            });
        }
        lines.push(['String ' + s, sc.toFixed(2), se.toFixed(4), String(cnt)].join(sep));
    }

    const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'pack-plan-battery-' + batteryId + '.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
    toastr.success('CSV file downloaded.', 'Export');
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
                    <div class="container-fluid mcc-pack-workspace py-2">
                        <div class="row g-3">
                            <div class="col-xl-2 col-lg-3 col-md-4">
                                <div class="mcc-pack-panel p-3 rounded-3 h-100">
                                    <h6 class="text-uppercase text-muted small mb-2">Project &amp; pool</h6>
                                    <div id="dropdown-container"></div>
                                    <div id="${leftListId}" class="list-group mcc-pack-cell-list mt-2"></div>
                                    <div class="control-panel mt-3">
                                        <label class="small text-muted d-block mb-1">Auto-pick by capacity (mAh)</label>
                                        <div class="d-flex flex-wrap gap-1 mb-2">
                                            <input type="number" id="min-capacity-input" class="form-control form-control-sm" placeholder="Min">
                                            <input type="number" id="max-capacity-input" class="form-control form-control-sm" placeholder="Max">
                                        </div>
                                        <button type="button" class="btn btn-sm btn-light w-100" id="auto-select-btn">Auto select</button>
                                    </div>
                                </div>
                            </div>
                            <div class="col-xl-2 col-lg-3 col-md-4">
                                <div class="mcc-pack-panel p-3 rounded-3 h-100">
                                    <h6 id="transfer-cells-title" class="text-center text-uppercase text-muted small mb-2">Staging (0)</h6>
                                    <div id="${middleListId}" class="list-group mcc-pack-cell-list"></div>
                                    <button type="button" id="assign-btn" class="btn btn-sm btn-primary w-100 mt-2">Assign to grid</button>
                                </div>
                            </div>
                            <div class="col-xl-8 col-lg-6 col-md-12">
                                <div class="mcc-pack-panel p-3 rounded-3">
                                    <div class="row g-3">
                                        <div class="col-lg-5">
                                            <h6 class="small text-uppercase text-muted mb-2">Scan label (QR)</h6>
                                            <input type="text" id="qr-scan-input" class="form-control form-control-sm mb-3" placeholder="Wedge scanner — Enter after scan" autocomplete="off">
                                            <h6 class="small text-uppercase text-muted mb-2">Manual UUID</h6>
                                            <input type="text" id="uuid-search" class="form-control form-control-sm mb-3" placeholder="Partial UUID">
                                            <div id="battery-controls" class="d-flex flex-wrap gap-2">
                                                <button type="button" class="btn btn-sm btn-light" id="reset-btn">Reset</button>
                                                <button type="button" class="btn btn-sm btn-outline-info" id="export-pack-plan-btn" title="Export balance plan CSV">Export CSV</button>
                                                <button type="button" class="btn btn-sm btn-secondary" id="save-draft-btn">Save draft</button>
                                                <button type="button" class="btn btn-sm btn-primary" id="finalize-pack-btn">Finalize pack</button>
                                            </div>
                                        </div>
                                        <div class="col-lg-7">
                                            <div id="battery-pack-container"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        `;

    $(accordionRow).insertAfter($triggerRow).show(function() {
        fetch('/get-battery-cells/?bat_id=' + encodeURIComponent(batteryId))
            .then(function (r) {
                if (!r.ok) {
                    toastr.error('Could not load pack data.', 'Error');
                    return Promise.reject(new Error('pack load'));
                }
                return r.json();
            })
            .then(function (meta) {
                if (meta.error) {
                    toastr.error(meta.error, 'Error');
                    return;
                }
                new Sortable(document.getElementById(leftListId), { group: 'shared', animation: 150 });
                new Sortable(document.getElementById(middleListId), { group: 'shared', animation: 150 });

                var projList = projects;
                if (typeof projects === 'string') {
                    try {
                        projList = JSON.parse(projects);
                    } catch (e) {
                        projList = [];
                    }
                }

                var draftPid = meta.draftProjectId;
                var initialName = '';
                if (draftPid) {
                    projList.forEach(function (p) {
                        if (String(p.id) === String(draftPid)) {
                            initialName = p.name;
                        }
                    });
                }

                var dropdown = createProjectDropdown(projList, batteryId, draftPid, initialName);
                document.getElementById('dropdown-container').appendChild(dropdown);

                var batteryLayout = createBatteryLayout(series, parallel);
                document.getElementById('battery-pack-container').appendChild(batteryLayout);
                makeBatterySortable();

                populateSlotsFromPackMeta(meta.cells);

                if (draftPid) {
                    fetchCells(String(draftPid), batteryId);
                }

                function runPackSave(isDraft) {
                    var pid = getSelectedPackProjectId();
                    if (!pid) {
                        toastr.warning('Select a project for this pack.', 'Pack');
                        return;
                    }
                    var payload = {
                        batteryId: batteryId,
                        cellsData: collectPackCellsData(),
                        isDraft: isDraft,
                        projectId: parseInt(pid, 10)
                    };
                    fetch('/save-battery-configuration/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify(payload)
                    })
                        .then(function (res) {
                            return res.json().then(function (data) {
                                if (!res.ok) {
                                    toastr.error(data.message || 'Save failed', 'Pack');
                                    return;
                                }
                                toastr.success(data.message || 'OK', 'Pack');
                                if (!isDraft) {
                                    window.location.reload();
                                }
                            });
                        })
                        .catch(function (err) {
                            console.error(err);
                            toastr.error('Network error', 'Pack');
                        });
                }

                document.getElementById('save-draft-btn').addEventListener('click', function () {
                    runPackSave(true);
                });
                document.getElementById('finalize-pack-btn').addEventListener('click', function () {
                    runPackSave(false);
                });
                document.getElementById('export-pack-plan-btn').addEventListener('click', function () {
                    exportPackPlanCsv(batteryId, series, parallel);
                });

                var qrInput = document.getElementById('qr-scan-input');
                qrInput.addEventListener('keydown', function (ev) {
                    if (ev.key !== 'Enter') {
                        return;
                    }
                    ev.preventDefault();
                    var raw = qrInput.value.trim();
                    qrInput.value = '';
                    var uuidPrefix = parseQrToCellUuidPrefix(raw);
                    if (!uuidPrefix) {
                        return;
                    }
                    var li = findListItemByUuidPrefix(uuidPrefix);
                    if (!li) {
                        toastr.error('Cell not found in list or pack. Check project selection.', 'QR');
                        return;
                    }
                    var targetS = pickTargetStringIndex(li, series, parallel);
                    if (targetS == null) {
                        toastr.warning('All strings are full.', 'Pack');
                        return;
                    }
                    highlightStringRow(targetS);
                    if (!moveCellToFirstFreeSlotInString(li, targetS, parallel)) {
                        toastr.warning('Could not place in string ' + targetS + '.', 'Pack');
                        return;
                    }
                    updateAllCapacities();
                    toastr.info('Placed in string (row) ' + targetS, 'QR');
                });

                var searchInput = document.getElementById('uuid-search');
                searchInput.addEventListener('input', function () {
                    highlightCell(this.value.trim(), required_cells_count);
                });
                searchInput.addEventListener('keypress', function (event) {
                    if (event.key === 'Enter') {
                        event.preventDefault();
                        highlightCell(this.value.trim(), required_cells_count);
                        this.select();
                    }
                });

                document.getElementById('auto-select-btn').addEventListener('click', function () {
                    var minCapacity = parseFloat(document.getElementById('min-capacity-input').value);
                    var maxCapacity = parseFloat(document.getElementById('max-capacity-input').value);
                    var leftListItems = document.querySelectorAll('#left-list .list-group-item');
                    var middleList = document.getElementById('middle-list');
                    var neededItemsCount = calculateNeededItems(required_cells_count);

                    leftListItems.forEach(function (item) {
                        var itemCapacity = parseFloat(item.dataset.capacity);
                        if ((itemCapacity >= minCapacity && itemCapacity <= maxCapacity) && neededItemsCount > 0) {
                            middleList.appendChild(item);
                            neededItemsCount--;
                        }
                    });

                    updateLeftListUI();
                });

                document.getElementById('assign-btn').addEventListener('click', function () {
                    assignCellsToPack(series, parallel);
                });

                capacityUpdateInterval = setInterval(updateAllCapacities, 1000);

                document.getElementById('reset-btn').addEventListener('click', function () {
                    var slots = document.querySelectorAll('.sortable-cell');
                    var middleList = document.getElementById('middle-list');

                    slots.forEach(function (slot) {
                        while (slot.firstChild) {
                            middleList.appendChild(slot.firstChild);
                        }
                    });

                    updateAllCapacities();
                });
            })
            .catch(function (e) {
                console.error(e);
                toastr.error('Could not load pack state.', 'Error');
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

    // Second pass: balance ESR sums across strings (same swap structure)
    let esrs = seriesArrays.map(function (s) {
        return s.reduce(function (t, c) { return t + parseFloat(c.dataset.esr || 0); }, 0);
    });
    for (let a = 0; a < series; a++) {
        for (let b = a + 1; b < series; b++) {
            for (let i = 0; i < parallel; i++) {
                for (let j = 0; j < parallel; j++) {
                    let newEsrA = esrs[a] - parseFloat(seriesArrays[a][i].dataset.esr || 0) + parseFloat(seriesArrays[b][j].dataset.esr || 0);
                    let newEsrB = esrs[b] - parseFloat(seriesArrays[b][j].dataset.esr || 0) + parseFloat(seriesArrays[a][i].dataset.esr || 0);
                    let newVar = Math.abs(newEsrA - newEsrB);
                    let curVar = Math.abs(esrs[a] - esrs[b]);
                    if (newVar < curVar) {
                        let temp = seriesArrays[a][i];
                        seriesArrays[a][i] = seriesArrays[b][j];
                        seriesArrays[b][j] = temp;
                        esrs[a] = newEsrA;
                        esrs[b] = newEsrB;
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






function deleteBatteries(batteryIds, cellDisposition) {
    cellDisposition = cellDisposition || 'release';
    fetch('/delete-batteries/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            battery_ids: batteryIds,
            cell_disposition: cellDisposition
        })
    })
        .then(function (response) { return response.json(); })
        .then(function () {
            window.location.reload();
        })
        .catch(function (error) { console.error('Error:', error); });
}

document.getElementById('deleteCellsBtn').addEventListener('click', function () {
    const checkedBoxes = document.querySelectorAll('input[name="battery_ids"]:checked');
    if (checkedBoxes.length === 0) {
        toastr.error('No battery packs selected', 'Error');
        return;
    }
    const batteryIds = Array.from(checkedBoxes).map(function (box) { return box.value; });
    showBulkDeleteConfirmation(batteryIds);
});

function showBulkDeleteConfirmation(batteryIds) {
    document.getElementById('deletePackModalText').textContent =
        'Delete ' + batteryIds.length + ' battery pack(s)? Choose what happens to assigned cells.';
    var modalEl = document.getElementById('deletePackModal');
    modalEl.dataset.pendingBatteryIds = JSON.stringify(batteryIds);
    new bootstrap.Modal(modalEl, { keyboard: false }).show();
}

function showDeleteConfirmation(batteryId) {
    document.getElementById('deletePackModalText').textContent =
        'Delete this battery pack? Choose what happens to assigned cells.';
    var modalEl = document.getElementById('deletePackModal');
    modalEl.dataset.pendingBatteryIds = JSON.stringify([String(batteryId)]);
    new bootstrap.Modal(modalEl, { keyboard: false }).show();
}

$(document).on('click', '.deleteBatteryBtn', function (e) {
    e.preventDefault();
    showDeleteConfirmation($(this).data('battery-id'));
});

function openEditBatteryModal(batteryId) {
    fetch('/battery/' + batteryId + '/detail/')
        .then(function (r) {
            if (!r.ok) throw new Error('load');
            return r.json();
        })
        .then(function (data) {
            document.getElementById('edit-battery-id').value = data.id;
            document.getElementById('edit-battery-name').value = data.name || '';
            document.getElementById('edit-battery-notes').value = data.notes || '';
            document.getElementById('edit-battery-pack-esr').value =
                data.pack_esr != null && data.pack_esr !== '' ? data.pack_esr : '';
            document.getElementById('edit-battery-mfg').value = data.manufacturing_date || '';
            new bootstrap.Modal(document.getElementById('editBatteryModal')).show();
        })
        .catch(function () {
            toastr.error('Could not load pack details.', 'Error');
        });
}

$(document).on('click', '.editBatteryBtn', function (e) {
    e.preventDefault();
    openEditBatteryModal($(this).data('battery-id'));
});

var saveEditBatteryBtnEl = document.getElementById('saveEditBatteryBtn');
if (saveEditBatteryBtnEl) saveEditBatteryBtnEl.addEventListener('click', function () {
    var id = document.getElementById('edit-battery-id').value;
    var pe = document.getElementById('edit-battery-pack-esr').value;
    fetch('/update-battery/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            battery_id: parseInt(id, 10),
            name: document.getElementById('edit-battery-name').value,
            notes: document.getElementById('edit-battery-notes').value,
            pack_esr: pe === '' ? null : pe,
            manufacturing_date: document.getElementById('edit-battery-mfg').value || null
        })
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.status === 'error') {
                toastr.error(data.message || 'Save failed', 'Error');
                return;
            }
            toastr.success(data.message || 'Saved', 'Success');
            bootstrap.Modal.getInstance(document.getElementById('editBatteryModal')).hide();
            window.location.reload();
        })
        .catch(function () {
            toastr.error('Save failed.', 'Error');
        });
});

var confirmPackDeleteBtnEl = document.getElementById('confirmPackDeleteBtn');
if (confirmPackDeleteBtnEl) confirmPackDeleteBtnEl.addEventListener('click', function () {
    var modalEl = document.getElementById('deletePackModal');
    var raw = modalEl.dataset.pendingBatteryIds;
    if (!raw) return;
    var ids;
    try {
        ids = JSON.parse(raw);
    } catch (e) {
        return;
    }
    var dispositionEl = document.querySelector('input[name="pack_cell_disposition"]:checked');
    var disposition = dispositionEl ? dispositionEl.value : 'release';
    deleteBatteries(ids, disposition);
    var inst = bootstrap.Modal.getInstance(modalEl);
    if (inst) inst.hide();
    modalEl.removeAttribute('data-pending-battery-ids');
});




async function sendAction(action) {
    const checkedBoxes = document.querySelectorAll('input[name="battery_ids"]:checked');
    const batteryIds = Array.from(checkedBoxes).map(function (box) { return box.value; });

    if (batteryIds.length === 0) {
        toastr.error('Please select one or more battery packs', 'Error');
        return;
    }

    if (action === 'print') {
        const cellSlots = [];
        for (let b = 0; b < batteryIds.length; b++) {
            const bid = batteryIds[b];
            const r = await fetch('/get-battery-cells/?bat_id=' + encodeURIComponent(bid));
            const data = await r.json();
            if (data.cells) {
                data.cells.forEach(function (c) {
                    cellSlots.push(c.id);
                });
            }
        }
        if (cellSlots.length === 0) {
            toastr.warning('No cells assigned to the selected batteries.', 'Print');
            return;
        }

        const doubleLabel = parseInt(includedValue($('#doubleLabel')), 10);

        if (doubleLabel === 1) {
            const batchSize = 2;
            if (cellSlots.length > 1) {
                for (let i = 0; i <= cellSlots.length - batchSize; i += batchSize) {
                    const batch = cellSlots.slice(i, i + batchSize);
                    printLabels(batch, -1);
                    await sleep(1000);
                }
                if (cellSlots.length % batchSize !== 0) {
                    printLabels(cellSlots.slice(-1), -1);
                }
            } else if (cellSlots.length === 1) {
                printLabels(cellSlots[0], -1);
            }
        } else {
            for (let i = 0; i < cellSlots.length; i++) {
                printLabels(cellSlots[i], -1);
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



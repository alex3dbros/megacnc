/**
 * Web Worker for Battery Pack Balancing
 * Runs serpentine distribution + swap balancing off the main thread
 * so the UI stays responsive.
 */

// Helper: Calculate standard deviation
function calculateStdDev(values) {
    if (values.length === 0) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map(v => Math.pow(v - mean, 2));
    return Math.sqrt(squaredDiffs.reduce((a, b) => a + b, 0) / values.length);
}

// Calculate parallel resistance for a group using pre-computed inverse sum
function calculateGroupResistanceFromCells(cellIndices, cells) {
    let sumInverseR = 0;
    for (let idx of cellIndices) {
        const esr = cells[idx].esr || 1;
        sumInverseR += 1 / esr;
    }
    return sumInverseR > 0 ? 1 / sumInverseR : 0;
}

self.onmessage = function(e) {
    const { cells, series, parallel } = e.data;
    const requiredCells = series * parallel;

    if (cells.length < requiredCells) {
        self.postMessage({ type: 'error', message: `Nicht genug Zellen. Benötigt: ${requiredCells}, Verfügbar: ${cells.length}` });
        return;
    }

    // ===== PHASE 1: Serpentine Distribution =====
    self.postMessage({ type: 'progress', phase: 'Serpentine', text: 'Sortiere Zellen...', progress: 5 });

    // Sort by capacity descending
    const sortedIndices = Array.from({ length: cells.length }, (_, i) => i);
    sortedIndices.sort((a, b) => cells[b].capacity - cells[a].capacity);

    // Use only the top requiredCells
    const usedIndices = sortedIndices.slice(0, requiredCells);

    // seriesAssignment[s] = array of cell indices assigned to series s
    let seriesAssignment = Array.from({ length: series }, () => []);
    let cellIndex = 0;

    for (let p = 0; p < parallel; p++) {
        const forward = (p % 2 === 0);
        for (let step = 0; step < series && cellIndex < usedIndices.length; step++) {
            const s = forward ? step : (series - 1 - step);
            seriesAssignment[s].push(usedIndices[cellIndex]);
            cellIndex++;
        }
    }

    self.postMessage({ type: 'progress', phase: 'Serpentine', text: 'Verteilung abgeschlossen', progress: 30 });

    // ===== PHASE 2: Swap Balancing with Incremental Score =====
    self.postMessage({ type: 'progress', phase: 'Balancing', text: 'Swap-Optimierung startet...', progress: 32 });

    // Pre-compute capacity sums and resistance for each series group
    let capacitySums = new Float64Array(series);
    let resistances = new Float64Array(series);

    for (let s = 0; s < series; s++) {
        let capSum = 0;
        for (let idx of seriesAssignment[s]) {
            capSum += cells[idx].capacity;
        }
        capacitySums[s] = capSum;
        resistances[s] = calculateGroupResistanceFromCells(seriesAssignment[s], cells);
    }

    function computeScore() {
        const capStdDev = calculateStdDev(Array.from(capacitySums));
        const resStdDev = calculateStdDev(Array.from(resistances));
        return (0.6 * capStdDev / 100) + (0.4 * resStdDev * 100);
    }

    // Incremental: recompute only groups a and b after a swap
    function recomputeGroupResistance(s) {
        resistances[s] = calculateGroupResistanceFromCells(seriesAssignment[s], cells);
    }

    const maxIterations = 100;
    const earlyStopThreshold = 0.005;
    let improved = true;
    let iteration = 0;
    let totalSwaps = 0;

    let initialScore = computeScore();
    let previousScore = initialScore;

    while (improved && iteration < maxIterations) {
        improved = false;
        iteration++;

        let currentScore = computeScore();
        let iterationSwaps = 0;

        for (let a = 0; a < series; a++) {
            for (let b = a + 1; b < series; b++) {
                for (let i = 0; i < seriesAssignment[a].length; i++) {
                    for (let j = 0; j < seriesAssignment[b].length; j++) {
                        const cellA = seriesAssignment[a][i];
                        const cellB = seriesAssignment[b][j];
                        const capA = cells[cellA].capacity;
                        const capB = cells[cellB].capacity;

                        // Quick check: if same capacity, no improvement possible
                        if (capA === capB) continue;

                        // Save old values
                        const oldCapSumA = capacitySums[a];
                        const oldCapSumB = capacitySums[b];
                        const oldResA = resistances[a];
                        const oldResB = resistances[b];

                        // Apply swap
                        seriesAssignment[a][i] = cellB;
                        seriesAssignment[b][j] = cellA;
                        capacitySums[a] = oldCapSumA - capA + capB;
                        capacitySums[b] = oldCapSumB - capB + capA;
                        recomputeGroupResistance(a);
                        recomputeGroupResistance(b);

                        const newScore = computeScore();

                        if (newScore < currentScore) {
                            currentScore = newScore;
                            improved = true;
                            totalSwaps++;
                            iterationSwaps++;
                        } else {
                            // Revert swap
                            seriesAssignment[a][i] = cellA;
                            seriesAssignment[b][j] = cellB;
                            capacitySums[a] = oldCapSumA;
                            capacitySums[b] = oldCapSumB;
                            resistances[a] = oldResA;
                            resistances[b] = oldResB;
                        }
                    }
                }
            }
        }

        const improvement = previousScore > 0 ? ((previousScore - currentScore) / previousScore) * 100 : 0;

        if (improved && improvement < earlyStopThreshold && iteration > 5) {
            break;
        }

        previousScore = currentScore;

        // Send progress update every iteration
        const progress = 32 + (iteration / maxIterations) * 60;
        const scoreReduction = ((initialScore - currentScore) / initialScore * 100).toFixed(1);
        self.postMessage({
            type: 'progress',
            phase: 'Balancing',
            text: `Iter ${iteration} | ${totalSwaps} Swaps | Score -${scoreReduction}%`,
            progress: Math.min(progress, 92)
        });
    }

    // ===== PHASE 3: Build result =====
    self.postMessage({ type: 'progress', phase: 'Finalisierung', text: 'Berechne Statistiken...', progress: 95 });

    const finalCapacities = [];
    const finalResistances = [];
    for (let s = 0; s < series; s++) {
        finalCapacities.push(capacitySums[s]);
        finalResistances.push(resistances[s]);
    }
    const capStdDev = calculateStdDev(finalCapacities);
    const resStdDev = calculateStdDev(finalResistances);

    // Build assignment map: seriesAssignment[s][p] = original cell index
    self.postMessage({
        type: 'result',
        assignment: seriesAssignment,
        stats: {
            iterations: iteration,
            swaps: totalSwaps,
            capStdDev: capStdDev,
            resStdDev: resStdDev,
            cells: requiredCells
        }
    });
};

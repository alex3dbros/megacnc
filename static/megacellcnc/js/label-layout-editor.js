/**
 * Label layout editor v2: canvas (px) + draggable elements (normalized 0–1).
 * Font popover appears inline above selected field.
 */
(function () {
    'use strict';

    var DEFAULT_BAT = {
        v: 2,
        layout_mode: 'absolute',
        canvas_w_px: 520,
        canvas_h_px: 360,
        use_template_bg: false,
        qr_box_size: 9,
        qr_border: 3,
        elements: {
            header: { x: 0.03, y: 0.03, w: 0.62, h: 0.11, font: 15, role: 'header', show: true },
            name_cap: { x: 0.03, y: 0.14, w: 0.58, h: 0.12, font: 12, role: 'body', show: true },
            config: { x: 0.03, y: 0.26, w: 0.58, h: 0.09, font: 12, role: 'body', show: true },
            esr: { x: 0.03, y: 0.35, w: 0.58, h: 0.08, font: 12, role: 'body', show: true },
            notes: { x: 0.03, y: 0.43, w: 0.58, h: 0.12, font: 10, role: 'small', show: true },
            mfg: { x: 0.03, y: 0.55, w: 0.55, h: 0.07, font: 10, role: 'small', show: true },
            custom: { x: 0.03, y: 0.62, w: 0.55, h: 0.07, font: 10, role: 'small', show: true },
            brand: { x: 0.03, y: 0.90, w: 0.62, h: 0.08, font: 12, role: 'small', show: true },
            qr: { x: 0.62, y: 0.48, size: 0.36, show: true }
        }
    };

    var DEFAULT_CELL = {
        v: 2,
        layout_mode: 'absolute',
        canvas_w_px: 400,
        canvas_h_px: 280,
        use_template_bg: false,
        qr_box_size: 9,
        qr_border: 3,
        elements: {
            header: { x: 0.03, y: 0.04, w: 0.62, h: 0.12, font: 15, role: 'header', show: true },
            esr_temp: { x: 0.03, y: 0.16, w: 0.58, h: 0.1, font: 12, role: 'body', show: true },
            voltages: { x: 0.03, y: 0.26, w: 0.58, h: 0.09, font: 12, role: 'body', show: true },
            mc_slot: { x: 0.03, y: 0.35, w: 0.58, h: 0.09, font: 12, role: 'body', show: true },
            date: { x: 0.03, y: 0.44, w: 0.55, h: 0.08, font: 10, role: 'small', show: true },
            custom: { x: 0.03, y: 0.52, w: 0.55, h: 0.08, font: 10, role: 'small', show: true },
            brand: { x: 0.03, y: 0.90, w: 0.62, h: 0.08, font: 12, role: 'small', show: true },
            qr: { x: 0.6, y: 0.42, size: 0.38, show: true }
        }
    };

    var DEFAULT_SQUARE = {
        v: 2,
        layout_mode: 'absolute',
        canvas_w_px: 500,
        canvas_h_px: 480,
        use_template_bg: false,
        qr_box_size: 9,
        qr_border: 3,
        elements: {
            header: { x: 0.04, y: 0.02, w: 0.60, h: 0.10, font: 15, role: 'header', show: true },
            esr_temp: { x: 0.04, y: 0.12, w: 0.55, h: 0.08, font: 12, role: 'body', show: true },
            voltages: { x: 0.04, y: 0.20, w: 0.55, h: 0.08, font: 12, role: 'body', show: true },
            mc_slot: { x: 0.04, y: 0.28, w: 0.55, h: 0.08, font: 12, role: 'body', show: true },
            date: { x: 0.04, y: 0.36, w: 0.50, h: 0.07, font: 10, role: 'small', show: true },
            custom: { x: 0.04, y: 0.43, w: 0.50, h: 0.07, font: 10, role: 'small', show: true },
            brand: { x: 0.03, y: 0.94, w: 0.62, h: 0.05, font: 12, role: 'small', show: true },
            qr: { x: 0.02, y: 0.50, size: 0.42, show: true }
        }
    };

    var BAT_LABELS = {
        header: 'PACK header', name_cap: 'Name + mAh', config: 'Config + S/N',
        esr: 'ESR', notes: 'Notes', mfg: 'Mfg', custom: 'Custom', brand: 'Brand', qr: 'QR'
    };
    var CELL_LABELS = {
        header: 'Serial + C', esr_temp: 'I / T', voltages: 'V min/store/max',
        mc_slot: 'Mc slot', date: 'Date', custom: 'Custom', brand: 'Brand', qr: 'QR'
    };
    var SQUARE_LABELS = CELL_LABELS;

    var BAT_DEMO_TEXT = {
        header: 'PACK 000001-C:3245', name_cap: 'Preview pack name\n3245 mAh',
        config: '3S3P  000001', esr: 'ESR: 0.12',
        notes: 'Notes preview — two lines if the box is wide enough.',
        mfg: 'Mfg: 2026-03-21', custom: 'custom.site.com (preview)', brand: 'deepcyclepower.com'
    };
    var CELL_DEMO_TEXT = {
        header: '000001-C:3245\nmAh', esr_temp: 'I:0.1 T:25',
        voltages: '2.8 / 3.7 / 4.24', mc_slot: 'Mc: 104-1',
        date: '2024-02-23', custom: 'custom.site.com (preview)', brand: 'deepcyclepower.com'
    };
    var SQUARE_DEMO_TEXT = CELL_DEMO_TEXT;

    function escapeHtml(s) {
        if (!s) return '';
        var d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    var batteryLayout = null;
    var cellLayout = null;
    var squareLayout = null;
    var selectedBatKey = null;
    var selectedCellKey = null;
    var selectedSqKey = null;

    function normalizeBrandInLayout(L) {
        if (!L || !L.elements) return;
        if (!L.elements.brand) {
            L.elements.brand = { x: 0.03, y: 0.94, w: 0.62, h: 0.05, font: 12, role: 'small', show: true };
        }
        var b = L.elements.brand;
        b.show = true;
        if (!parseInt(b.font, 10) || parseInt(b.font, 10) < 12) b.font = 12;
        var q = L.elements.qr;
        if (q && q.show !== false) {
            var qBottom = (parseFloat(q.y) || 0) + (parseFloat(q.size) || 0);
            if (b.y < qBottom && b.y + (b.h || 0.05) > parseFloat(q.y || 0)) {
                b.y = Math.min(qBottom + 0.01, 0.96);
                b.h = Math.min(b.h || 0.05, 1.0 - b.y - 0.01);
            }
        }
    }

    function clone(o) { return JSON.parse(JSON.stringify(o)); }

    function mergeLayout(base, patch) {
        var out = clone(base);
        if (!patch || typeof patch !== 'object') return out;
        Object.keys(patch).forEach(function (k) {
            if (k === 'elements' && patch.elements && typeof patch.elements === 'object') {
                out.elements = out.elements || {};
                Object.keys(patch.elements).forEach(function (ek) {
                    if (out.elements[ek] && typeof patch.elements[ek] === 'object') {
                        Object.assign(out.elements[ek], patch.elements[ek]);
                    } else {
                        out.elements[ek] = patch.elements[ek];
                    }
                });
            } else if (patch[k] !== undefined) {
                out[k] = patch[k];
            }
        });
        return out;
    }

    function layoutFor(kind) {
        if (kind === 'battery') return batteryLayout;
        if (kind === 'square') return squareLayout;
        return cellLayout;
    }
    function prefixFor(kind) {
        if (kind === 'battery') return 'bat';
        if (kind === 'square') return 'sq';
        return 'cell';
    }
    function labelsFor(kind) {
        if (kind === 'battery') return BAT_LABELS;
        if (kind === 'square') return SQUARE_LABELS;
        return CELL_LABELS;
    }
    function demosFor(kind) {
        if (kind === 'battery') return BAT_DEMO_TEXT;
        if (kind === 'square') return SQUARE_DEMO_TEXT;
        return CELL_DEMO_TEXT;
    }
    function hostIdFor(kind) {
        if (kind === 'battery') return 'bat-canvas-host';
        if (kind === 'square') return 'sq-canvas-host';
        return 'cell-canvas-host';
    }

    function syncInputsFromState(kind) {
        var L = layoutFor(kind);
        var p = prefixFor(kind);
        var wEl = document.getElementById(p + '-canvas-w');
        var hEl = document.getElementById(p + '-canvas-h');
        var bgEl = document.getElementById(p + '-use-bg');
        if (wEl) wEl.value = L.canvas_w_px;
        if (hEl) hEl.value = L.canvas_h_px;
        if (bgEl) bgEl.checked = !!L.use_template_bg;
    }

    function readCanvasFromInputs(kind) {
        var p = prefixFor(kind);
        var L = layoutFor(kind);
        var w = parseInt(document.getElementById(p + '-canvas-w').value, 10);
        var h = parseInt(document.getElementById(p + '-canvas-h').value, 10);
        if (w >= 120 && w <= 1200) L.canvas_w_px = w;
        if (h >= 80 && h <= 900) L.canvas_h_px = h;
        var bgEl = document.getElementById(p + '-use-bg');
        if (bgEl) L.use_template_bg = bgEl.checked;
    }

    function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }

    function dragBounds(meta, key, cw, ch) {
        var rot = (parseInt(meta.rotate, 10) || 0) % 360;
        if (key === 'qr') {
            var sw = meta.size * Math.min(cw, ch) / cw;
            var sh = meta.size * Math.min(cw, ch) / ch;
            return { xMin: 0, xMax: 1 - sw, yMin: 0, yMax: 1 - sh };
        }
        var w = meta.w || 0, h = meta.h || 0;
        if (rot === 90 || rot === 270) {
            return {
                xMin: (h - w) / 2,
                xMax: 1 - (w + h) / 2,
                yMin: (w - h) / 2,
                yMax: 1 - (w + h) / 2
            };
        }
        return { xMin: 0, xMax: 1 - w, yMin: 0, yMax: 1 - h };
    }

    /* ── Selection & inline font popover ─────────────────────── */

    function setSelectedField(kind, key) {
        if (kind === 'battery') selectedBatKey = key;
        else if (kind === 'square') selectedSqKey = key;
        else selectedCellKey = key;
        applySelectionHighlight(kind);
        showFontPopover(kind);
    }

    function selectedKeyFor(kind) {
        if (kind === 'battery') return selectedBatKey;
        if (kind === 'square') return selectedSqKey;
        return selectedCellKey;
    }

    function applySelectionHighlight(kind) {
        var host = document.getElementById(hostIdFor(kind));
        if (!host) return;
        var sel = selectedKeyFor(kind);
        host.querySelectorAll('.mcc-lc-box').forEach(function (box) {
            box.classList.toggle('mcc-lc-selected', box.dataset.key === sel);
        });
    }

    function removeFontPopover(host) {
        var old = host.querySelector('.mcc-lc-font-pop');
        if (old) old.remove();
    }

    function showFontPopover(kind) {
        var L = layoutFor(kind);
        var labels = labelsFor(kind);
        var host = document.getElementById(hostIdFor(kind));
        if (!host) return;
        var canvas = host.querySelector('.mcc-lc-canvas');
        if (!canvas) return;
        removeFontPopover(host);

        var sel = selectedKeyFor(kind);
        if (!sel || sel === 'qr') return;

        var meta = L.elements[sel];
        if (!meta) return;
        var isBrand = sel === 'brand';

        var box = host.querySelector('.mcc-lc-box[data-key="' + sel + '"]');
        if (!box) return;

        var pop = document.createElement('div');
        pop.className = 'mcc-lc-font-pop';

        var lbl = document.createElement('label');
        lbl.textContent = (labels[sel] || sel) + ' pt';
        var inp = document.createElement('input');
        inp.type = 'number';
        inp.min = isBrand ? 12 : 0;
        inp.max = 80;
        inp.value = isBrand ? Math.max(12, parseInt(meta.font, 10) || 12) : (meta.font || 0);

        function apply() {
            var v = parseInt(inp.value, 10);
            if (isNaN(v)) return;
            if (isBrand) {
                meta.font = clamp(v, 12, 80);
            } else {
                meta.font = clamp(v, 0, 80);
            }
            inp.value = meta.font;
        }
        inp.addEventListener('change', apply);
        inp.addEventListener('blur', apply);
        inp.addEventListener('pointerdown', function (e) { e.stopPropagation(); });

        var rotBtn = document.createElement('button');
        rotBtn.type = 'button';
        rotBtn.className = 'mcc-lc-rot-btn';
        rotBtn.title = 'Rotate 90\u00B0';
        rotBtn.textContent = '\u21BB';
        rotBtn.addEventListener('pointerdown', function (e) { e.stopPropagation(); });
        rotBtn.addEventListener('click', function () {
            meta.rotate = ((parseInt(meta.rotate, 10) || 0) + 90) % 360;
            applyBoxRotation(box, meta.rotate);
        });

        pop.appendChild(lbl);
        pop.appendChild(inp);
        if (!isBrand) pop.appendChild(rotBtn);

        if (isBrand) {
            pop.style.position = 'relative';
            pop.style.left = '0';
            pop.style.top = '0';
            pop.style.marginBottom = '4px';
            pop.style.display = 'inline-flex';
            box.after(pop);
        } else {
            canvas.appendChild(pop);
            var bx = parseFloat(box.style.left) || 0;
            var by = parseFloat(box.style.top) || 0;
            pop.style.left = bx + '%';
            pop.style.top = 'calc(' + by + '% - 28px)';
            if (by < 8) {
                var bh = parseFloat(box.style.height) || 5;
                pop.style.top = 'calc(' + (by + bh) + '% + 4px)';
            }
        }

        setTimeout(function () { inp.focus(); inp.select(); }, 30);
    }

    function applyBoxRotation(box, deg) {
        if (!deg) {
            box.style.transform = '';
        } else {
            box.style.transform = 'rotate(' + deg + 'deg)';
        }
    }

    /* ── Canvas rendering ────────────────────────────────────── */

    function renderCanvas(kind) {
        var L = layoutFor(kind);
        normalizeBrandInLayout(L);
        var host = document.getElementById(hostIdFor(kind));
        var labels = labelsFor(kind);
        var demos = demosFor(kind);
        if (!host || !L) return;

        var cw = L.canvas_w_px;
        var ch = L.canvas_h_px;
        host.innerHTML = '';
        var canvas = document.createElement('div');
        canvas.className = 'mcc-lc-canvas';
        canvas.style.aspectRatio = cw + ' / ' + ch;
        canvas.style.width = '100%';

        Object.keys(L.elements || {}).forEach(function (key) {
            if (key === 'brand') return;
            var meta = L.elements[key];
            if (!meta || meta.show === false) return;

            var box = document.createElement('div');
            box.className = 'mcc-lc-box' + (key === 'qr' ? ' mcc-lc-qr' : '');
            box.dataset.key = key;

            if (key === 'qr') {
                box.textContent = 'QR';
            } else {
                var tit = document.createElement('div');
                tit.className = 'mcc-lc-tit';
                tit.textContent = labels[key] || key;
                var demo = document.createElement('div');
                demo.className = 'mcc-lc-demo';
                demo.innerHTML = escapeHtml(demos[key] || '').replace(/\n/g, '<br>');
                box.appendChild(tit);
                box.appendChild(demo);
            }

            if (key === 'qr') {
                var rz = document.createElement('div');
                rz.className = 'mcc-lc-resize';
                rz.dataset.key = key;
                box.appendChild(rz);
            } else {
                var rzw = document.createElement('div');
                rzw.className = 'mcc-lc-resize-wh';
                rzw.dataset.key = key;
                box.appendChild(rzw);
            }

            if (key === 'qr') {
                var s = meta.size * Math.min(cw, ch);
                box.style.left = (meta.x * 100) + '%';
                box.style.top = (meta.y * 100) + '%';
                box.style.width = ((s / cw) * 100) + '%';
                box.style.height = ((s / ch) * 100) + '%';
            } else {
                box.style.left = (meta.x * 100) + '%';
                box.style.top = (meta.y * 100) + '%';
                box.style.width = (meta.w * 100) + '%';
                box.style.height = (meta.h * 100) + '%';
            }

            if (key !== 'qr') {
                applyBoxRotation(box, parseInt(meta.rotate, 10) || 0);
            }

            canvas.appendChild(box);
        });

        var brandBar = document.createElement('div');
        brandBar.className = 'mcc-lc-box mcc-lc-brand-locked';
        brandBar.dataset.key = 'brand';
        var brandTit = document.createElement('div');
        brandTit.className = 'mcc-lc-tit';
        brandTit.textContent = 'BRAND';
        var brandDemo = document.createElement('div');
        brandDemo.className = 'mcc-lc-demo';
        brandDemo.textContent = 'deepcyclepower.com';
        brandBar.appendChild(brandTit);
        brandBar.appendChild(brandDemo);
        brandBar.addEventListener('pointerdown', function () {
            setSelectedField(kind, 'brand');
        });
        host.appendChild(brandBar);
        host.appendChild(canvas);

        attachInteractions(canvas, L, kind);
        applySelectionHighlight(kind);
        showFontPopover(kind);
    }

    /* ── Drag & resize interactions ──────────────────────────── */

    function attachInteractions(canvas, L, kind) {
        var cw = L.canvas_w_px;
        var ch = L.canvas_h_px;

        canvas.addEventListener('click', function (ev) {
            if (ev.target === canvas) setSelectedField(kind, null);
        });

        canvas.querySelectorAll('.mcc-lc-box').forEach(function (box) {
            var key = box.dataset.key;

            box.addEventListener('pointerdown', function (ev) {
                if (ev.target.classList.contains('mcc-lc-resize') || ev.target.classList.contains('mcc-lc-resize-wh')) return;
                if (ev.target.closest('.mcc-lc-font-pop')) return;
                setSelectedField(kind, key);
                ev.preventDefault();
                box.setPointerCapture(ev.pointerId);
                var rect = canvas.getBoundingClientRect();
                var meta = L.elements[key];
                var ox = ev.clientX, oy = ev.clientY;
                var sx = meta.x, sy = meta.y;
                var bounds = dragBounds(meta, key, cw, ch);

                function onMove(ev2) {
                    meta.x = clamp(sx + (ev2.clientX - ox) / rect.width, bounds.xMin, bounds.xMax);
                    meta.y = clamp(sy + (ev2.clientY - oy) / rect.height, bounds.yMin, bounds.yMax);
                    box.style.left = (meta.x * 100) + '%';
                    box.style.top = (meta.y * 100) + '%';
                    showFontPopover(kind);
                }
                function onUp() {
                    box.releasePointerCapture(ev.pointerId);
                    window.removeEventListener('pointermove', onMove);
                    window.removeEventListener('pointerup', onUp);
                }
                window.addEventListener('pointermove', onMove);
                window.addEventListener('pointerup', onUp);
            });
        });

        canvas.querySelectorAll('.mcc-lc-resize').forEach(function (rz) {
            rz.addEventListener('pointerdown', function (ev) {
                ev.stopPropagation(); ev.preventDefault();
                var key = rz.dataset.key;
                setSelectedField(kind, key);
                var meta = L.elements[key];
                var rect = canvas.getBoundingClientRect();
                var ox = ev.clientX, oy = ev.clientY, os = meta.size;
                function onMove(ev2) {
                    var d = ((ev2.clientX - ox) / rect.width + (ev2.clientY - oy) / rect.height) / 2;
                    meta.size = clamp(os + d * 2.5, 0.15, 0.65);
                    var s = meta.size * Math.min(cw, ch);
                    rz.parentElement.style.width = ((s / cw) * 100) + '%';
                    rz.parentElement.style.height = ((s / ch) * 100) + '%';
                }
                function onUp() {
                    window.removeEventListener('pointermove', onMove);
                    window.removeEventListener('pointerup', onUp);
                }
                window.addEventListener('pointermove', onMove);
                window.addEventListener('pointerup', onUp);
            });
        });

        canvas.querySelectorAll('.mcc-lc-resize-wh').forEach(function (rz) {
            rz.addEventListener('pointerdown', function (ev) {
                ev.stopPropagation(); ev.preventDefault();
                var key = rz.dataset.key;
                setSelectedField(kind, key);
                var meta = L.elements[key];
                var rect = canvas.getBoundingClientRect();
                var ox = ev.clientX, oy = ev.clientY;
                var ow = meta.w, oh = meta.h;
                function onMove(ev2) {
                    meta.w = clamp(ow + (ev2.clientX - ox) / rect.width, 0.05, 1 - meta.x);
                    meta.h = clamp(oh + (ev2.clientY - oy) / rect.height, 0.03, 1 - meta.y);
                    rz.parentElement.style.width = (meta.w * 100) + '%';
                    rz.parentElement.style.height = (meta.h * 100) + '%';
                    showFontPopover(kind);
                }
                function onUp() {
                    window.removeEventListener('pointermove', onMove);
                    window.removeEventListener('pointerup', onUp);
                }
                window.addEventListener('pointermove', onMove);
                window.addEventListener('pointerup', onUp);
            });
        });
    }

    /* ── Preview ─────────────────────────────────────────────── */

    function previewImgIdFor(kind) {
        if (kind === 'battery') return 'previewBatteryImg';
        if (kind === 'square') return 'previewSquareImg';
        return 'previewCellImg';
    }

    function collectJsonFor(kind) {
        if (kind === 'battery') return collectBatteryLayoutJson();
        if (kind === 'square') return collectSquareLayoutJson();
        return collectCellLayoutJson();
    }

    function preview(kind) {
        var json = collectJsonFor(kind);
        return fetch('/preview-label-layout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': typeof getCookie === 'function' ? getCookie('csrftoken') : ''
            },
            body: JSON.stringify({ kind: kind, layout: JSON.parse(json) })
        })
        .then(function (r) { return r.json(); })
        .then(function (d) {
            if (d.label) {
                var im = document.getElementById(previewImgIdFor(kind));
                if (im) im.src = 'data:image/jpeg;base64,' + d.label;
            }
        })
        .catch(function (e) { console.error(e); });
    }

    /* ── Public API ──────────────────────────────────────────── */

    window.collectBatteryLayoutJson = function () {
        readCanvasFromInputs('battery');
        normalizeBrandInLayout(batteryLayout);
        return JSON.stringify(batteryLayout);
    };

    window.collectCellLayoutJson = function () {
        readCanvasFromInputs('cell');
        normalizeBrandInLayout(cellLayout);
        return JSON.stringify(cellLayout);
    };

    window.collectSquareLayoutJson = function () {
        readCanvasFromInputs('square');
        normalizeBrandInLayout(squareLayout);
        return JSON.stringify(squareLayout);
    };

    window.applyLabelLayoutsFromServer = function (data) {
        try {
            var b = JSON.parse(data.batteryLabelLayoutJson || '{}');
            batteryLayout = b.layout_mode === 'absolute' && b.elements ? mergeLayout(DEFAULT_BAT, b) : clone(DEFAULT_BAT);
        } catch (e) { batteryLayout = clone(DEFAULT_BAT); }
        try {
            var c = JSON.parse(data.cellLabelLayoutJson || '{}');
            cellLayout = c.layout_mode === 'absolute' && c.elements ? mergeLayout(DEFAULT_CELL, c) : clone(DEFAULT_CELL);
        } catch (e2) { cellLayout = clone(DEFAULT_CELL); }
        try {
            var sq = JSON.parse(data.squareLabelLayoutJson || '{}');
            squareLayout = sq.layout_mode === 'absolute' && sq.elements ? mergeLayout(DEFAULT_SQUARE, sq) : clone(DEFAULT_SQUARE);
        } catch (e3) { squareLayout = clone(DEFAULT_SQUARE); }
        normalizeBrandInLayout(batteryLayout);
        normalizeBrandInLayout(cellLayout);
        normalizeBrandInLayout(squareLayout);
        selectedBatKey = null;
        selectedCellKey = null;
        selectedSqKey = null;
        syncInputsFromState('battery');
        syncInputsFromState('cell');
        syncInputsFromState('square');
        renderCanvas('battery');
        renderCanvas('cell');
        renderCanvas('square');
    };

    /* ── Init ────────────────────────────────────────────────── */

    function bindEditorEvents(kind, defaultLayout) {
        var p = prefixFor(kind);
        var el = function (id) { return document.getElementById(id); };

        var applyBtn = el(p + '-apply-size');
        if (applyBtn) applyBtn.addEventListener('click', function () {
            readCanvasFromInputs(kind); renderCanvas(kind);
        });

        var prevBtn = el(p + '-preview-btn');
        if (prevBtn) prevBtn.addEventListener('click', function () {
            readCanvasFromInputs(kind); preview(kind);
        });

        var resetBtn = el(p + '-reset-btn');
        if (resetBtn) resetBtn.addEventListener('click', function () {
            if (kind === 'battery') { batteryLayout = clone(defaultLayout); selectedBatKey = null; }
            else if (kind === 'square') { squareLayout = clone(defaultLayout); selectedSqKey = null; }
            else { cellLayout = clone(defaultLayout); selectedCellKey = null; }
            syncInputsFromState(kind); renderCanvas(kind); preview(kind);
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        batteryLayout = clone(DEFAULT_BAT);
        cellLayout = clone(DEFAULT_CELL);
        squareLayout = clone(DEFAULT_SQUARE);
        syncInputsFromState('battery');
        syncInputsFromState('cell');
        syncInputsFromState('square');
        renderCanvas('battery');
        renderCanvas('cell');
        renderCanvas('square');

        bindEditorEvents('battery', DEFAULT_BAT);
        bindEditorEvents('cell', DEFAULT_CELL);
        bindEditorEvents('square', DEFAULT_SQUARE);

        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(function (tabBtn) {
            tabBtn.addEventListener('shown.bs.tab', function (e) {
                if (e.target && e.target.id === 'bat-layout-tab') renderCanvas('battery');
                if (e.target && e.target.id === 'cell-layout-tab') renderCanvas('cell');
                if (e.target && e.target.id === 'sq-layout-tab') renderCanvas('square');
            });
        });
    });
})();

"""
Absolute label layouts (v2): canvas size + normalized element boxes (0–1).
Battery packs default to a larger canvas than cells.
"""
import json

# Reference canvas for font auto-scaling when font_pt is 0
FONT_REF = 400.0

# Brand box in editor: position is pinned (server draws URL in a fixed bottom strip).
BRAND_ELEMENT_PINNED = {
    "x": 0.03,
    "y": 0.90,
    "w": 0.62,
    "h": 0.08,
}

# Battery: larger label by default
DEFAULT_BATTERY_ABSOLUTE = {
    "v": 2,
    "layout_mode": "absolute",
    "canvas_w_px": 520,
    "canvas_h_px": 360,
    "use_template_bg": False,
    "elements": {
        # font: pt for PIL; 0 = auto from canvas size. Defaults: header 15, body 12, small 10.
        "header": {"x": 0.03, "y": 0.03, "w": 0.62, "h": 0.11, "font": 15, "role": "header", "show": True},
        "name_cap": {"x": 0.03, "y": 0.14, "w": 0.58, "h": 0.12, "font": 12, "role": "body", "show": True},
        "config": {"x": 0.03, "y": 0.26, "w": 0.58, "h": 0.09, "font": 12, "role": "body", "show": True},
        "esr": {"x": 0.03, "y": 0.35, "w": 0.58, "h": 0.08, "font": 12, "role": "body", "show": True},
        "notes": {"x": 0.03, "y": 0.43, "w": 0.58, "h": 0.12, "font": 10, "role": "small", "show": True},
        "mfg": {"x": 0.03, "y": 0.55, "w": 0.55, "h": 0.07, "font": 10, "role": "small", "show": True},
        "custom": {"x": 0.03, "y": 0.62, "w": 0.55, "h": 0.07, "font": 10, "role": "small", "show": True},
        "brand": {"x": 0.03, "y": 0.90, "w": 0.62, "h": 0.08, "font": 12, "role": "small", "show": True},
        "qr": {"x": 0.62, "y": 0.48, "size": 0.36, "show": True},
    },
    "qr_box_size": 9,
    "qr_border": 3,
}

# Cell landscape: smaller default canvas
DEFAULT_CELL_ABSOLUTE = {
    "v": 2,
    "layout_mode": "absolute",
    "canvas_w_px": 400,
    "canvas_h_px": 280,
    "use_template_bg": False,
    "elements": {
        "header": {"x": 0.03, "y": 0.04, "w": 0.62, "h": 0.12, "font": 15, "role": "header", "show": True},
        "esr_temp": {"x": 0.03, "y": 0.16, "w": 0.58, "h": 0.10, "font": 12, "role": "body", "show": True},
        "voltages": {"x": 0.03, "y": 0.26, "w": 0.58, "h": 0.09, "font": 12, "role": "body", "show": True},
        "mc_slot": {"x": 0.03, "y": 0.35, "w": 0.58, "h": 0.09, "font": 12, "role": "body", "show": True},
        "date": {"x": 0.03, "y": 0.44, "w": 0.55, "h": 0.08, "font": 10, "role": "small", "show": True},
        "custom": {"x": 0.03, "y": 0.52, "w": 0.55, "h": 0.08, "font": 10, "role": "small", "show": True},
        "brand": {"x": 0.03, "y": 0.60, "w": 0.55, "h": 0.08, "font": 12, "role": "small", "show": True},
        "qr": {"x": 0.60, "y": 0.42, "size": 0.38, "show": True},
    },
    "qr_box_size": 9,
    "qr_border": 3,
}


# Cell square: taller canvas, QR bottom-left, text top
DEFAULT_SQUARE_ABSOLUTE = {
    "v": 2,
    "layout_mode": "absolute",
    "canvas_w_px": 500,
    "canvas_h_px": 480,
    "use_template_bg": False,
    "elements": {
        "header":   {"x": 0.04, "y": 0.02, "w": 0.60, "h": 0.10, "font": 15, "role": "header", "show": True},
        "esr_temp": {"x": 0.04, "y": 0.12, "w": 0.55, "h": 0.08, "font": 12, "role": "body",   "show": True},
        "voltages": {"x": 0.04, "y": 0.20, "w": 0.55, "h": 0.08, "font": 12, "role": "body",   "show": True},
        "mc_slot":  {"x": 0.04, "y": 0.28, "w": 0.55, "h": 0.08, "font": 12, "role": "body",   "show": True},
        "date":     {"x": 0.04, "y": 0.36, "w": 0.50, "h": 0.07, "font": 10, "role": "small",  "show": True},
        "custom":   {"x": 0.04, "y": 0.43, "w": 0.50, "h": 0.07, "font": 10, "role": "small",  "show": True},
        "brand":    {"x": 0.03, "y": 0.94, "w": 0.62, "h": 0.05, "font": 12, "role": "small",  "show": True},
        "qr":       {"x": 0.02, "y": 0.50, "size": 0.42, "show": True},
    },
    "qr_box_size": 9,
    "qr_border": 3,
}


def _sanitize_brand_in_elements(elements):
    """deepcyclepower.com is always printed; min 12 pt; show forced on."""
    if not isinstance(elements, dict):
        return
    b = elements.get("brand")
    if not isinstance(b, dict):
        elements["brand"] = dict(BRAND_ELEMENT_PINNED, font=12, role="small", show=True)
        return
    nb = dict(b)
    nb["show"] = True
    f = int(nb.get("font") or 0)
    if f < 12:
        nb["font"] = 12
    elements["brand"] = nb


def merge_absolute_defaults(kind, layout):
    """kind: 'battery' | 'cell' | 'square'. Merges user layout over defaults."""
    if kind == "battery":
        base = DEFAULT_BATTERY_ABSOLUTE
    elif kind == "square":
        base = DEFAULT_SQUARE_ABSOLUTE
    else:
        base = DEFAULT_CELL_ABSOLUTE
    out = json.loads(json.dumps(base))
    if not layout:
        return out
    if isinstance(layout, str):
        try:
            layout = json.loads(layout)
        except json.JSONDecodeError:
            return out
    if not isinstance(layout, dict):
        return out
    # shallow merge top-level
    for k, v in layout.items():
        if k == "elements" and isinstance(v, dict):
            for ek, ev in v.items():
                if ek in out["elements"] and isinstance(ev, dict):
                    out["elements"][ek].update(ev)
                else:
                    out["elements"][ek] = ev
        else:
            out[k] = v
    _sanitize_brand_in_elements(out.get("elements"))
    return out

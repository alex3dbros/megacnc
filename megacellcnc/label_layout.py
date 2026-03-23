"""
Default layouts and merge helpers for thermal label rendering (cells + battery packs).
Stored as JSON on PrinterSettings (CellLabelLayoutJson / BatteryLabelLayoutJson).
"""
import json
from .label_layout_absolute import merge_absolute_defaults

DEFAULT_BATTERY_LABEL_LAYOUT = {
    "v": 1,
    "qr_frac": 0.52,
    "qr_min_px": 150,
    "qr_max_px": 210,
    "text_qr_gap_px": 14,
    "margin_px": 10,
    "min_text_column_px": 130,
    "font_header_pt": 0,
    "font_body_pt": 0,
    "font_small_pt": 0,
    "qr_box_size": 9,
    "qr_border": 3,
    "show_header": True,
    "show_name_capacity": True,
    "show_config_serial": True,
    "show_esr": True,
    "show_notes": True,
    "show_mfg": True,
    "show_custom_footer": True,
    "show_brand_url": True,
}

DEFAULT_CELL_LABEL_LAYOUT = {
    "v": 1,
    "qr_frac": 0.52,
    "qr_min_px": 150,
    "qr_max_px": 210,
    "text_qr_gap_px": 14,
    "margin_px": 10,
    "min_text_column_px": 130,
    "font_header_pt": 0,
    "font_body_pt": 0,
    "font_small_pt": 0,
    "qr_box_size": 9,
    "qr_border": 3,
    "show_header": True,
    "show_esr_temp": True,
    "show_voltages": True,
    "show_mc_slot": True,
    "show_date": True,
    "show_custom_footer": True,
    "show_brand_url": True,
}

# Demo data for settings preview (no DB row required). Fill every field so the editor preview matches placement.
PREVIEW_BATTERY_LABEL_DICT = {
    "serial": 1,
    "serial_str": "000001",
    "uuid": "D20260321-S000001",
    "cap": 3245.0,
    "name": "Preview pack name",
    "esr": 0.12,
    "notes": "Notes preview — two lines if the box is wide enough.",
    "date": "2026-03-21",
    "configuration": "3S3P",
}

# Shown in label preview when PrinterSettings.CustomField1 is empty (layout editor only)
PREVIEW_BATTERY_CUSTOM_LINE = "custom.site.com (preview)"


def parse_layout_json(raw):
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    s = str(raw).strip()
    if not s:
        return {}
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return {}


def merge_battery_layout(layout):
    d = DEFAULT_BATTERY_LABEL_LAYOUT.copy()
    d.update(parse_layout_json(layout))
    return d


def merge_cell_layout(layout):
    d = DEFAULT_CELL_LABEL_LAYOUT.copy()
    d.update(parse_layout_json(layout))
    return d


def battery_layout_from_printer(printer):
    """Return layout dict for battery labels. Always returns v2 absolute layout."""
    raw = getattr(printer, "BatteryLabelLayoutJson", None) if printer else None
    parsed = parse_layout_json(raw)
    if parsed.get("layout_mode") == "absolute" and parsed.get("elements"):
        return parsed
    return merge_absolute_defaults('battery', parsed)


def cell_layout_from_printer(printer):
    """Return layout dict for cell labels. Always returns v2 absolute layout."""
    raw = getattr(printer, "CellLabelLayoutJson", None) if printer else None
    parsed = parse_layout_json(raw)
    if parsed.get("layout_mode") == "absolute" and parsed.get("elements"):
        return parsed
    return merge_absolute_defaults('cell', parsed)


def square_layout_from_printer(printer):
    """Return layout dict for square cell labels. Always returns v2 absolute layout."""
    raw = getattr(printer, "SquareLabelLayoutJson", None) if printer else None
    parsed = parse_layout_json(raw)
    if parsed.get("layout_mode") == "absolute" and parsed.get("elements"):
        return parsed
    return merge_absolute_defaults('square', parsed)

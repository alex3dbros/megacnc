#!/usr/bin/env python3
"""Test MCCPro get_chemistry / set_chemistry (safe: writes back slot-1 values)."""
import json
import sys

import requests

IP = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.35"
TIMEOUT = 12
HEADERS = {"content-type": "application/json"}


def post(path, data):
    url = f"http://{IP}/{path}"
    r = requests.post(url, data=json.dumps(data), headers=HEADERS, timeout=TIMEOUT)
    text = r.content.decode("utf-8", errors="replace")
    return r.status_code, text, r.content


def main():
    print(f"Target: {IP}\n")

    try:
        code, text, _ = post("api/who_am_i", {})
    except requests.RequestException as e:
        print(f"FAIL: Gerät nicht erreichbar – {e}")
        sys.exit(1)

    print(f"who_am_i [{code}]: {text.strip()[:200]}")
    if code != 200:
        sys.exit(1)

    code, text, _ = post("api/get_chemistry", {"CiD": 0})
    print(f"get_chemistry [{code}]: {text.strip()[:200]}")

    try:
        code, text, _ = post("api/get_cells_info", {"start": 1, "end": 1})
        info = json.loads(text)
        cell = info["cells"][0]
    except Exception as e:
        print(f"get_cells_info FAIL: {e}")
        sys.exit(1)

    print(f"Slot 1: MaV={cell.get('MaV')} MiV={cell.get('MiV')} StV={cell.get('StV')}")

    def mv(v, default):
        if v is None:
            return default
        v = float(v)
        return int(round(v * 1000)) if v < 10 else int(round(v))

    payload = {
        "Chem": {
            "id": 5,
            "name": "MegaCNC-Test",
            "maxVolt": mv(cell.get("MaV"), 4200),
            "minVolt": mv(cell.get("MiV"), 2800),
            "sVolt": mv(cell.get("StV"), 3700),
            "maxCap": 4500,
            "chgCur": 2000,
            "pChgCur": 128,
            "terChgCur": 128,
            "dchgCur": 500,
            "dchgRes": 1,
            "dchgMod": 0,
            "maxTemp": 35,
            "LmR": 120,
            "McH": 300,
            "DiC": int(cell.get("DiC") or 1),
        },
        "CiD": 0,
    }

    print("\nset_chemistry (gleiche Werte wie Slot 1)...")
    try:
        code, text, raw = post("api/set_chemistry", payload)
    except requests.Timeout:
        print("FAIL: set_chemistry TIMEOUT – Endpoint hängt oder FW antwortet nicht")
        sys.exit(2)
    except requests.RequestException as e:
        print(f"FAIL: set_chemistry – {e}")
        sys.exit(1)

    print(f"set_chemistry [{code}] len={len(raw)}: {text.strip()[:300] or '(leer)'}")

    if code == 404 or "not found" in text.lower():
        print("\nErgebnis: set_chemistry existiert in dieser Firmware NICHT")
        sys.exit(3)
    if code == 200 and "not found" not in text.lower():
        print("\nErgebnis: set_chemistry antwortet OK")
        sys.exit(0)
    print(f"\nErgebnis: unklar (HTTP {code})")
    sys.exit(4)


if __name__ == "__main__":
    main()

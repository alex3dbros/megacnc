# MCCPro API Reference (v1.1.0)

Integration guide for external software (MegaCNC, custom clients).

Base URL: `http://<device-ip>/`

---

## Device Identification

### GET /api/who_am_i

Returns device info.

**Response:**
```json
{
  "ChT": "MCCPro",
  "FwV": "1.1.0",
  "McA": "AA:BB:CC:DD:EE:FF",
  "CeC": 16
}
```

| Field | Type   | Description              |
|-------|--------|--------------------------|
| ChT   | string | Charger type             |
| FwV   | string | Firmware version         |
| McA   | string | MAC address              |
| CeC   | int    | Cell/group count         |

---

## Cell Data

### POST /api/get_cells_info

Returns detailed cell data. This is the **legacy endpoint** used by MegaCNC.

**Request body:**
```json
{ "start": 1, "end": 16 }
```

| Field | Type | Description                        |
|-------|------|------------------------------------|
| start | int  | First cell (1-based, min 1)        |
| end   | int  | Last cell (inclusive, max 16)       |

**Response:**
```json
{
  "cells": [
    {
      "CiD": 0,
      "VlT": 4.182,
      "AmP": 500,
      "CaP": 1.234,
      "CCa": 2.100,
      "StS": "Started Charging",
      "esr": 0.045,
      "AcL": 1.500,
      "DiC": 1,
      "CoC": 0,
      "TmP": 25.300,
      "ChC": false,
      "CcO": 1,
      "DcO": 1,
      "MaV": 4.200,
      "StV": 3.700,
      "MiV": 2.800,
      "GiD": 0,
      "StT": "Not Set"
    }
  ]
}
```

| Field | Type   | Description                              |
|-------|--------|------------------------------------------|
| CiD   | int    | Cell ID (0-based)                        |
| VlT   | float  | Voltage in V (e.g. 4.182)               |
| AmP   | int    | Current in mA                            |
| CaP   | float  | Discharge capacity in mAh               |
| CCa   | float  | Charge capacity in mAh                  |
| StS   | string | State name (see State Table below)       |
| esr   | float  | ESR in ohms                              |
| AcL   | float  | Total runtime in hours                   |
| DiC   | int    | Set discharge cycles                     |
| CoC   | int    | Completed discharge cycles               |
| TmP   | float  | Temperature in C                         |
| ChC   | bool   | Always false (reserved)                  |
| CcO   | int    | Always 1 (reserved)                      |
| DcO   | int    | Always 1 (reserved)                      |
| MaV   | float  | Max voltage in V                         |
| StV   | float  | Store voltage in V                       |
| MiV   | float  | Min voltage in V                         |
| GiD   | int    | Group ID                                 |
| StT   | string | Always "Not Set" (reserved)              |

### GET /api/dash_data

Lightweight endpoint used by the web dashboard. Returns compact data with minimal overhead.

**Response:**
```json
{
  "sys": {
    "heap": 5000,
    "frag": 12,
    "rssi": -65,
    "fan": 1,
    "temp": 25.3,
    "chem": "Li-Ion",
    "act": 8,
    "cg": 16,
    "mcg": 1,
    "gc": 16
  },
  "cells": [
    [8, 4182, 500, 2100, 1234, 0, 25.3],
    [0, 0, 0, 0, 0, 1, 0.0]
  ]
}
```

**sys object:**

| Field | Type   | Description                      |
|-------|--------|----------------------------------|
| heap  | int    | Free heap bytes                  |
| frag  | int    | Heap fragmentation %             |
| rssi  | int    | WiFi RSSI in dBm                 |
| fan   | int    | Fan state (0=off, 1=on)          |
| temp  | float  | Temperature of cell 0            |
| chem  | string | Active chemistry name or "Mixed" |
| act   | int    | Number of inserted cells         |
| cg    | int    | Cells to group setting           |
| mcg   | int    | Max cells per group              |
| gc    | int    | Total group count                |

**cells array** (each cell is a compact array):

`[state, voltage_mV, current_mA, charge_cap_mAh, discharge_cap_mAh, group_id, temperature_C]`

| Index | Type  | Description                 |
|-------|-------|-----------------------------|
| 0     | int   | State ID (see State Table)  |
| 1     | int   | Voltage in mV               |
| 2     | int   | Current in mA               |
| 3     | int   | Charge capacity in mAh      |
| 4     | int   | Discharge capacity in mAh   |
| 5     | int   | Group ID                    |
| 6     | float | Temperature in C            |

---

## Cell States

| ID | Enum Name          | Display Name            |
|----|--------------------|-------------------------|
| 0  | NOT_INSERTED       | Not Inserted            |
| 1  | CELL_INSERTED      | Cell inserted           |
| 2  | CHECK_CHEMISTRY    | Checking Chemistry      |
| 3  | LVC_CELL           | LVC Cell                |
| 4  | REGULAR_CELL       | Regular Cell            |
| 5  | BAD_VC_READING     | Bad VC Reading          |
| 6  | TOO_COLD           | Too Cold                |
| 7  | LVC_CHARGE         | LVC Charging            |
| 8  | REGULAR_CHARGE     | Started Charging        |
| 9  | COOLDOWN           | Cooldown                |
| 10 | CHARGING_FAILED    | Charging Failed         |
| 11 | CHARGED_CHECK      | Checking if Charged     |
| 12 | VOLT_DROP_CHECK    | Volt Drop Check         |
| 13 | CHARGED            | Charged                 |
| 14 | ANORMAL_CHARGED    | Anormal Charged         |
| 15 | BAD_CELL           | Bad Cell                |
| 16 | DISCHARGE          | Started Discharging     |
| 17 | DISCHARGED         | Discharged              |
| 18 | DISCHARGE_FAILED   | Discharge Failed        |
| 19 | ESR_READ           | ESR Reading             |
| 20 | ESR_READ_COMPLETED | ESR Read Completed      |
| 21 | ESR_READ_FAILED    | ESR Read Failed         |
| 22 | RESTING            | Resting                 |
| 23 | RESTED             | Rested                  |
| 24 | CHECK_STORE_ACTION | Checking Store Action   |
| 25 | STORE_CHARGING     | Started Store Charging  |
| 26 | STORE_DISCHARGING  | Started Store Discharging |
| 27 | STORE_CHECK        | Checking If Stored      |
| 28 | STORED             | Stored                  |
| 29 | FAILED_STORE       | Failed Store            |
| 30 | DISPOSE            | Dispose started         |
| 31 | DISPOSED           | Disposed                |
| 32 | ERROR              | Error                   |

---

## Cell Commands

### POST /api/set_cell

Send commands to one or more cells. To avoid memory issues, send max 2 cells per request.

**Request body:**
```json
{
  "cells": [
    { "CiD": 0, "CmD": "ach" },
    { "CiD": 1, "CmD": "ach" }
  ]
}
```

| CmD  | Action              |
|------|---------------------|
| ach  | Start charging      |
| adc  | Start discharging   |
| sc   | Stop charging       |
| osc  | Stop charging (alt) |
| odc  | Stop discharging    |
| esr  | ESR measurement     |
| dsp  | Dispose             |
| dps  | Stop disposing      |
| cdc  | Reset cell data     |
| ccc  | Reset cell data (alt) |
| asc  | Store               |

**Response:** `success` or `failed`

### POST /api/set_cell_macro

Send macro commands. Same format as set_cell, max 2 cells per request.

**Request body:**
```json
{
  "cells": [
    { "CiD": 0, "CmD": "mCap" }
  ]
}
```

| CmD  | Action                                    |
|------|-------------------------------------------|
| mCap | Measure capacity (charge-discharge cycle)  |
| stop | Stop macro                                 |

**Response:** `success` or `failed`

---

## Chemistry Management

### GET /api/chemistries

Returns available chemistry presets and the active chemistry name.

**Response:**
```json
{
  "active": "Li-Ion",
  "presets": [
    {
      "id": 1,
      "name": "Li-Ion",
      "maxV": 4200,
      "minV": 2800,
      "stoV": 3700,
      "maxCap": 5000,
      "chgI": 1000,
      "preI": 128,
      "trmI": 128,
      "dchI": 1000,
      "dchR": 1.0,
      "dchM": 0,
      "maxT": 50,
      "lvT": 120,
      "mcT": 240,
      "cyc": 1
    }
  ]
}
```

### POST /api/apply_chem

Apply a preset chemistry or a custom chemistry to all cells.

**Apply preset:**
```json
{ "preset": "Li-Ion" }
```

**Apply custom:**
```json
{
  "name": "Custom",
  "maxV": 4200,
  "minV": 2800,
  "stoV": 3700,
  "maxCap": 5000,
  "chgI": 1000,
  "preI": 128,
  "trmI": 128,
  "dchI": 1000,
  "dchR": 1.0,
  "dchM": 0,
  "maxT": 50,
  "lvT": 120,
  "mcT": 240,
  "cyc": 1
}
```

| Field | Type  | Description                      |
|-------|-------|----------------------------------|
| maxV  | int   | Max voltage in mV                |
| minV  | int   | Min voltage in mV                |
| stoV  | int   | Store voltage in mV              |
| maxCap| int   | Max capacity in mAh              |
| chgI  | int   | Charging current in mA           |
| preI  | int   | Pre-charge current in mA         |
| trmI  | int   | Termination current in mA        |
| dchI  | int   | Discharge current in mA          |
| dchR  | float | Discharge resistance in ohms     |
| dchM  | int   | Discharge mode (0=current, 1=resistance) |
| maxT  | int   | Max temperature in C             |
| lvT   | int   | Low voltage recovery time in min |
| mcT   | int   | Max charge time in min           |
| cyc   | int   | Discharge cycles                 |

**Response:** `OK` or `FAIL`

### POST /api/set_chemistry

Set chemistry for a specific cell (legacy endpoint).

**Request body:**
```json
{
  "CiD": 0,
  "Chem": {
    "id": 1,
    "name": "Li-Ion",
    "maxVolt": 4200,
    "minVolt": 2800,
    "sVolt": 3700,
    "maxCap": 5000,
    "chgCur": 1000,
    "pChgCur": 128,
    "terChgCur": 128,
    "dchgCur": 1000,
    "dchgRes": 1.0,
    "dchgMod": 0,
    "maxTemp": 50,
    "LmR": 120,
    "McH": 240,
    "DiC": 1
  }
}
```

---

## Settings

### GET /api/settings

Returns current device settings.

**Response:**
```json
{
  "hw": { "fan": 0, "temp": 0, "cg": 16, "mcg": 1 },
  "menu": { "wifi": 1, "ota": 1, "cycle": 1 },
  "net": { "conn": 1, "rssi": -55, "ip": "192.168.1.127", "ssid": "MyWiFi", "mac": "AA:BB:CC:DD:EE:FF" }
}
```

### POST /api/save_hw

Save hardware settings.

```json
{ "fan": false, "temp": 0, "cg": 16, "mcg": 1 }
```

| Field | Type | Description                            |
|-------|------|----------------------------------------|
| fan   | bool | Manual fan override                    |
| temp  | int  | Temperature source                     |
| cg    | int  | Cells to group (1-16)                  |
| mcg   | int  | Max cells per group                    |

### POST /api/save_menu

Save menu settings.

```json
{ "wifi": true, "ota": true, "cycle": true }
```

### POST /api/set_hw_conf

Alternative hardware config endpoint (legacy).

```json
{
  "tempSource": 0,
  "cellsToGroup": 16,
  "maxCellPerGroup": 1,
  "dataFeedType": 0
}
```

---

## System

### POST /api/reboot

Reboots the device. No body required.

### POST /api/do_factory_reset

Factory reset and reboot. No body required.

---

## OTA Updates

### POST /api/update

Upload firmware binary. Multipart form upload with file field.

### POST /api/update_spiffs

Upload SPIFFS filesystem image. Multipart form upload with file field. Config files are backed up and restored automatically.

---

## Important Notes for Integration

1. **Memory constraints**: The ESP8266 has limited RAM (~5-6KB free heap during operation). Avoid sending requests faster than every 250ms. Batch cell commands in groups of 2.

2. **Rate limiting**: The device returns HTTP 503 with body `low memory` when heap is critically low. Clients should retry after 1-2 seconds.

3. **MegaCNC compatibility**: The `/api/get_cells_info` endpoint returns the full verbose JSON format with string field names (`VlT`, `AmP`, `StS`, etc.) as used by MegaCNC. The `/api/dash_data` endpoint is a compact alternative used by the built-in web dashboard.

4. **Connection**: The device runs on port 80. All responses use `Connection: close`.

5. **Cell IDs**: Cell IDs are 0-based (0-15) in all endpoints. The `get_cells_info` `start` parameter is 1-based but internal IDs are 0-based.

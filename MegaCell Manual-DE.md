# Giga CN - Benutzerhandbuch

## Übersicht

Giga CN (Fork von MegaCell CNC) ist eine Webanwendung zur Verwaltung von Batteriezellen-Tests und Battery Pack-Konfiguration.

---

## 1. Dashboard (Home)

Die Startseite zeigt:
- **Total Cells**: Gesamtzahl aller getesteten Zellen
- **Good Cells**: Zellen mit erfolgreichem Test
- **Total Projects**: Anzahl der Projekte
- **Projects-Tabelle**: Übersicht aller Projekte
- **Devices-Tabelle**: Übersicht aller registrierten Testgeräte

---

## 2. Projects

### Zweck
Projekte organisieren Zellen nach Herkunft oder Verwendungszweck (z.B. "Samsung 30Q Batch 1", "Recycling Laptop-Akkus").

### Funktionen
- **+ Add Project**: Neues Projekt erstellen
  - Project Name
  - Cell Type (18650, 21700, LifePo4, Other)
  - Notes

### Anzeige
| Spalte | Beschreibung |
|--------|-------------|
| Project Name | Name des Projekts (klickbar für Details) |
| Device Count | Anzahl zugewiesener Testgeräte |
| Creation Date | Erstellungsdatum |
| Notes | Notizen |
| Status | Active/Inactive |
| Total Cells | Anzahl getesteter Zellen |

---

## 3. Devices

### Zweck
Testgeräte (MegaCell CNC Hardware) verwalten.

### Funktionen

#### + Add Device
1. IP-Range definieren (z.B. 192.168.1.1 - 192.168.1.255)
2. Oder manuelle IP eingeben
3. "Scan for Devices" klicken
4. Device Prefix setzen (z.B. "MCC-")
5. Projekt zuweisen
6. "Add Device" klicken

#### Edit Device (Stift-Icon)
| Einstellung | Beschreibung |
|-------------|-------------|
| Device Name | Gerätename |
| Chemistry | Voreingestelltes Profil |
| Min Voltage | Entlade-Endspannung |
| Store Voltage | Lagerspannung |
| Max Voltage | Lade-Endspannung |
| Chg Current | Ladestrom (mA) |
| Dischg Current | Entladestrom (mA) |
| Max Temp | Temperaturlimit (°C) |
| Cycles | Anzahl Lade/Entlade-Zyklen |
| Chg Timeout | Lade-Timeout (Minuten) |
| Discharge Mode | CC/CV/CR |
| Cells to group | Slots für Gruppierung |
| Cells per group | Zellen pro Gruppe |

#### Delete Device (Papierkorb-Icon)
Löscht das Gerät aus der Datenbank.

---

## 4. Device Slots

### Zweck
Einzelne Slots eines Testgeräts überwachen und steuern.

### Statusübersicht
- Not Inserted, Regular Cells, Low Voltage Cells
- Charging, Discharging, Stored, Bad

### Slot-Tabelle
| Spalte | Beschreibung |
|--------|-------------|
| # | Slot-Nummer |
| V | Aktuelle Spannung |
| C | Aktueller Strom (mA) |
| ESR | Innenwiderstand (mΩ) |
| Capacity | Entladekapazität (mAh) |
| Charge Cap | Ladekapazität (mAh) |
| State | Aktueller Zustand |
| Runtime | Laufzeit der Aktion |
| Cycles | Abgeschlossene/Gesetzte Zyklen |
| Temp | Temperatur (°C) |
| Max/Store/Min V | Gesetzte Spannungen |
| Cell ID | Zell-UUID |

### Aktionen (Buttons)

| Button | Funktion |
|--------|----------|
| **Charge** | Lädt auf Max-Spannung |
| **Discharge** | Entlädt auf Min-Spannung |
| **Store** | Bringt auf Lagerspannung |
| **ESR** | Misst Innenwiderstand |
| **Dispose** | Entlädt auf 1V (sichere Entsorgung) |
| **Stop** | Stoppt aktuelle Aktion |
| **Macro** | Automatisch: Charge → Discharge → Store |
| **Stop Macro** | Bricht Makro ab |
| **Print** | Druckt Labels |

### Slot-Details (+ Button)
Zeigt erweiterte Testdaten und Verlaufsgrafik.

### Zelle speichern (Disketten-Icon)
Speichert den abgeschlossenen Test in der Datenbank. Die Zelle erhält eine UUID und ist danach für Battery Packs verfügbar.

---

## 5. Database

### Zweck
Übersicht aller getesteten Zellen mit Filter- und Bearbeitungsfunktionen.

### Spalten
| Spalte | Beschreibung |
|--------|-------------|
| ID | Datenbank-ID |
| Serial No | Cell-ID (aus UUID) |
| Available | Verfügbar für Packs (Yes/No) |
| Condition | Zustand der Zelle |
| Project | Zugehöriges Projekt |
| Type | Zelltyp (18650, 21700, etc.) |
| Capacity | Gemessene Kapazität (mAh) |
| ESR | Innenwiderstand (mΩ) |
| Test Date | Datum des Tests |

### Condition (Zellenzustand)

Neues Feld zur Klassifizierung von Zellen:

| Zustand | Farbe | Bedeutung |
|---------|-------|-----------|
| **Gut** | 🟢 Grün | Normal, verwendbar |
| **Defekt** | 🔴 Rot | Beschädigt, nicht verwenden |
| **Reserviert** | 🟡 Gelb | Für bestimmten Zweck reserviert |
| **Unbekannt** | ⚫ Grau | Status unklar |

### Bulk-Edit (Massenbearbeitung)

Mehrere Zellen gleichzeitig bearbeiten:

1. **Zellen auswählen** (Checkboxen links)
2. **Tag-Icon** klicken (erscheint bei Auswahl)
3. **Status wählen**:
   - Condition: Gut / Defekt / Reserviert / Unbekannt
   - Available: Yes / No

### Filter & Suche

| Filter | Funktion |
|--------|----------|
| **Serial Search** | Suche nach Cell-ID |
| **Project** | Nur Zellen eines Projekts |
| **Year** | Nach Testjahr filtern |
| **Status** | Available/Not Available |

### Spalten ein-/ausblenden

Klick auf **Spalten-Icon** → Checkboxen für jede Spalte.

---

## 6. Batteries

### Zweck
Battery Packs aus getesteten Zellen zusammenstellen.

### Begriffe
- **Series**: Reihenschaltung (addiert Spannung)
- **Parallel**: Parallelschaltung (addiert Kapazität)
- Beispiel: 2S2P = 2 Reihen, 2 parallel = 4 Zellen total

### Haupttabelle
| Spalte | Beschreibung |
|--------|-------------|
| ID | Batterie-ID |
| Available | Verfügbar (Yes/No) |
| Name | Batteriename |
| Series | Anzahl Reihen |
| Parallel | Anzahl parallel |
| Required Cells | Benötigte Zellen (Series × Parallel) |
| Assigned Cells | Zugewiesene Zellen |
| Capacity | Gesamtkapazität |
| Status | Created/Complete |
| Creation Date | Erstellungsdatum |

### + Add Battery
- **Battery Name**: z.B. "E-Bike Pack 1"
- **Series**: Anzahl Reihenschaltungen
- **Parallel**: Anzahl Parallelschaltungen

### Battery Pack Editor (+ Button)

#### Linke Seite - Zellenauswahl
1. **Select Project**: Projekt wählen → lädt verfügbare Zellen
2. **Min Capacity (mAh)**: Mindestkapazität Filter
3. **Max Capacity (mAh)**: Maximalkapazität Filter
4. **Auto Select**: Wählt automatisch passende Zellen aus (siehe Sampling-Algorithmus)

#### Zellen-Anzeige
Jede Zelle zeigt: `Cell-ID - Kapazität mAh - ESR mΩ`
- **Cell-ID**: Nummer aus der UUID (z.B. 012559)
- **Kapazität**: Gemessene Entladekapazität
- **ESR**: Innenwiderstand in Milliohm

#### Mitte - Transfer Cells
- Zeigt Zellen, die zur Zuweisung bereit sind
- **Assign**: Verteilt Zellen automatisch auf das Pack

#### Rechte Seite - Battery Pack Layout
- **Reset Cells**: Alle Zellen zurück in Transfer-Liste
- **Save Pack**: Konfiguration in Datenbank speichern
- **Layout-Grid**: Drag & Drop zum manuellen Platzieren

#### Pack-Toolbar Buttons

| Button | Icon | Funktion |
|--------|------|----------|
| **Auto Select** | ✨ | Wählt Zellen automatisch aus |
| **Assign** | ✓ | Verteilt Zellen mit Balancing |
| **Reset** | ↩ | Setzt alle Zellen zurück |
| **Save** | 💾 | Speichert Pack-Konfiguration |
| **Chart** | 📊 | Zeigt grafische Analyse |
| **History** | 🕐 | Zeigt Ersetzungs-Historie |
| **Print** | 🖨️ | Druckt Labels für alle Pack-Zellen |
| **Export** | ⬇️ | Exportiert Zellenliste als CSV |
| **Auflösen** | 🗑️ | Löst Pack auf, gibt Zellen frei |

### Pack Export (CSV)

Der **Export-Button** erstellt eine CSV-Datei mit allen Zellen im Pack.

#### Inhalt
```csv
Cell-ID;UUID;Position;Capacity (mAh);ESR (mΩ);Voltage (V)
012559;D20230620-S012559;S1-P1;2450;12.5;3.65
012560;D20230620-S012560;S1-P2;2445;12.8;3.64
...

Total Cells;540
Total Capacity;1323000 mAh
Avg Capacity;2450.0 mAh
Avg ESR;12.34 mΩ
```

- Sortiert nach Cell-ID
- Zusammenfassung mit Totalen und Durchschnittswerten

### Pack Labels drucken

Der **Print-Button** druckt Labels für alle Zellen im aktuellen Pack.
- Verwendet die Drucker-Einstellungen aus Settings
- Unterstützt Single- und Dual-Label-Modus

### Multi-Objective Balancing-Algorithmus (Assign-Button)

Der erweiterte Algorithmus optimiert **zwei Metriken gleichzeitig**:

#### Optimierte Metriken

| Metrik | Formel | Ziel |
|--------|--------|------|
| **Gruppen-Kapazität** | Summe aller Zell-Kapazitäten | Alle Reihen gleiche Gesamtkapazität |
| **Gruppen-Widerstand** | 1 / Σ(1/R) (Parallelschaltung) | Alle Reihen gleichen Gesamtwiderstand |

#### Algorithmus-Phasen

**Phase 1: Serpentine-Verteilung**
- Zellen werden nach Kapazität sortiert
- Schlangenförmige Verteilung auf die Reihen (1→2→3→3→2→1→...)
- Erzeugt eine gute Ausgangsbalance

**Phase 2: Iteratives Multi-Objective Balancing**
- Berechnet Score: `(0.6 × StdDev_Kapazität) + (0.4 × StdDev_Widerstand)`
- Probiert Zellen-Tausch zwischen allen Reihen
- Tausch wird nur durchgeführt wenn der Score sinkt
- Wiederholt bis keine Verbesserung mehr möglich

#### Visuelle Animations-Feedback

Während des Balancings zeigt das Battery Layout:

| Phase | Visualisierung |
|-------|----------------|
| **Serpentine** | Zellen blinken gelb beim Platzieren, dann blau |
| **Swap** | Getauschte Zellen blinken orange |
| **Fertig** | Alle Zellen werden grün |

Der **Status-Banner** zeigt live:
- Aktuelle Phase (1 oder 2)
- Fortschritt in Prozent
- Anzahl Iterationen und Swaps
- Score-Reduktion (z.B. "-96.9%")

#### Score-Interpretation

Der Score misst die **Ungleichmässigkeit** zwischen den Serien:

| Score | Bedeutung |
|-------|-----------|
| **Hoch** | Serien unterscheiden sich stark (schlecht) |
| **Niedrig** | Serien sind ähnlich (gut) |

**Was bedeutet "-96.9%"?**

Das ist die **Reduktion** gegenüber dem Startwert:
- Initial Score: 10.0 (nach Serpentine)
- Final Score: 0.31 (nach Balancing)
- Reduktion: **-96.9%**

| Reduktion | Bewertung |
|-----------|-----------|
| < 50% | Wenig Potenzial (war schon gut) |
| 50-80% | Gute Verbesserung |
| 80-95% | Sehr gute Verbesserung |
| > 95% | Exzellent |

#### Kapazitäts-Abweichung (mAh StdDev)

Die **Standardabweichung** misst, wie unterschiedlich die Gesamtkapazitäten der Serien sind.

**Beispiel 10S4P Pack:**
- S1: 10'200 mAh, S2: 10'201 mAh, S3: 10'199 mAh...
- StdDev = 0.2 mAh → praktisch identisch

| StdDev | Bewertung |
|--------|-----------|
| < 1 mAh | Perfekt |
| 1-10 mAh | Sehr gut |
| 10-50 mAh | Gut |
| > 100 mAh | Verbesserungswürdig |

#### Widerstands-Abweichung (ESR StdDev)

| StdDev | Bewertung |
|--------|-----------|
| < 0.1 mΩ | Perfekt |
| 0.1-0.5 mΩ | Sehr gut |
| 0.5-1 mΩ | Gut |
| > 1 mΩ | Verbesserungswürdig |

#### Warum ESR-Balancing wichtig ist

Bei Parallelschaltung gilt:
- Zellen mit niedrigerem ESR liefern mehr Strom
- Ungleicher ESR → ungleiche Wärmeentwicklung
- Ungleicher ESR → unterschiedlicher "Voltage Sag" unter Last

**Ziel**: Alle Reihen sollen den gleichen mittleren Widerstand haben, damit sich Spannungseinbruch und Wärme gleichmässig verteilen.

### Repräsentatives Sampling (Auto Select)

Der Auto Select verwendet **äquidistantes Sampling** für nachhaltiges Bestandsmanagement:

#### Problem mit einfacher Auswahl
Wenn immer nur die "besten" Zellen gepickt werden, bleibt für zukünftige Projekte nur die "Resterampe" übrig.

#### Lösung: Äquidistante Auswahl
1. Zellen im gewählten Kapazitätsbereich filtern
2. Sortieren: Kapazität aufsteigend, dann ESR absteigend (schlechteste → beste)
3. Schrittweite berechnen: `step = Anzahl_Kandidaten / Benötigte_Zellen`
4. Zellen bei Index 0, step, 2×step, 3×step... auswählen

**Beispiel**: 1000 Zellen verfügbar, 100 benötigt → Nimmt Zelle 0, 10, 20, 30...

**Vorteil**: Das Pack enthält einen repräsentativen Mix aus dem gesamten Bestand.

### Ersatzzellen-Finder

Falls beim physischen Bau eine Zelle defekt wird (fallen gelassen, Lötproblem):

#### Kontextmenü (Rechtsklick)

**Rechtsklick auf eine Zelle im Battery Layout** öffnet ein Menü:

| Option | Funktion |
|--------|----------|
| **Zelle ersetzen** | Findet beste Ersatzzelle aus Reserve-Pool |
| **Details anzeigen** | Zeigt UUID, Kapazität, ESR, Spannung |
| **Zelle entfernen** | Verschiebt Zelle zurück in Transfer-Liste |

#### Matching-Kriterien
- **Delta Kapazität**: Differenz zur defekten Zelle minimieren
- **Delta ESR**: Differenz zum Innenwiderstand minimieren
- **Gewichtung**: 60% Kapazität, 40% ESR

#### Verwendung
1. **Rechtsklick** auf die defekte Zelle im Layout
2. "Zelle ersetzen" wählen
3. System findet automatisch die beste Ersatzzelle
4. Ersetzung wird protokolliert

#### Ersetzungs-Historie

Jede Zellen-Ersetzung wird automatisch in der Datenbank protokolliert:

| Feld | Beschreibung |
|------|-------------|
| Alte Zelle | UUID, Kapazität, ESR |
| Neue Zelle | UUID, Kapazität, ESR |
| Position | Serie (S) und Parallel (P) Slot |
| Zeitstempel | Wann ersetzt |
| Grund | z.B. "defective" |

**API zum Abrufen der Historie:**
```
GET /replacement-history/<battery_id>/
```

Dies ermöglicht volle Nachvollziehbarkeit aller Zellen-Änderungen im Pack.

### Pack Chart - Grafische Analyse

Der **Chart-Button** (📊) öffnet eine interaktive Grafik zur Analyse der Zellenwerte im Pack.

#### Funktionen
| Element | Beschreibung |
|---------|-------------|
| **Serien-Auswahl** | Multi-Select: Eine oder mehrere Serien zum Vergleich wählen |
| **Metrik-Toggle** | Capacity, ESR, Voltage einzeln ein-/ausblenden |
| **X-Achse** | Parallel-Slots (P1, P2, P3, ...) |
| **Y-Achsen** | Links: Capacity (mAh) / Rechts: ESR (mΩ), Voltage (V) |

#### Verwendung
1. Pack öffnen (Editor)
2. Chart-Button klicken
3. Serien auswählen (Mehrfachauswahl mit Strg/Cmd)
4. Metriken per Toggle ein-/ausblenden
5. Hover über Datenpunkte für Details

### Pack auflösen

Der **Pack auflösen**-Button gibt alle zugewiesenen Zellen wieder frei.

#### Ablauf
1. Button "Pack auflösen" klicken
2. Bestätigungsdialog erscheint
3. Bei Bestätigung: Alle Zellen werden freigegeben
4. Zellen sind wieder für andere Packs verfügbar

⚠️ **Achtung:** Diese Aktion kann nicht rückgängig gemacht werden!

### Workflow-Anzeige

Der Editor zeigt den aktuellen Workflow-Status:

| Schritt | Status |
|---------|--------|
| 1. Zellen auswählen | Auto Select oder manuell |
| 2. Zellen zuweisen | Assign-Button |
| 3. Speichern | Save-Button (pulsiert wenn ungespeichert) |

Nach dem Balancing erscheint ein **Result-Banner** mit:
- Balancing-Ergebnis (Score, Iterationen, Swaps)
- **Save**: Pack speichern
- **Reset**: Zellen zurücksetzen
- **Close**: Banner schliessen

### Checkpoint-System

Bei grossen Packs (500+ Zellen) wird der Balancing-Fortschritt automatisch gesichert.

#### Funktionen
- Automatische Speicherung nach jeder Iteration
- Bei Absturz/Reload: Dialog zur Wiederaufnahme
- Zeigt Score-Entwicklung während des Balancings

### Use Case: Battery Pack erstellen

1. **Batterie erstellen**: "+ Add Battery" → Name, Series, Parallel eingeben
2. **Editor öffnen**: Klick auf "+" bei der Batterie
3. **Projekt wählen**: Dropdown "Select Project" → Zellen laden
4. **Filter setzen**: Min/Max Capacity für gewünschten Bereich
5. **Auto Select**: Klicken → Zellen werden in Transfer-Liste verschoben
6. **Assign**: Klicken → automatische Verteilung mit Balancing
7. **Workflow beobachten**: Status-Banner zeigt Fortschritt
8. **Chart prüfen**: Grafische Analyse der Verteilung
9. **Save Pack**: Konfiguration speichern (Button pulsiert)

---

## 7. Settings

Die Settings-Seite ist in Tabs organisiert:

### Tab: Printer

Konfiguriert den Labeldrucker (z.B. Dymo).

#### Step 1: Verbindung
1. QZ Tray herunterladen und installieren (Button oben rechts)
2. "Connect" klicken
3. Drucker suchen:
   - "Find Printer" (nach Name, z.B. "dymo")
   - "Find Default Printer"
   - "Find All Printers"

#### Step 2: Label Settings
| Einstellung | Beschreibung |
|-------------|-------------|
| Dual Label | Für Dymo 13mm × 25mm Doppel-Labels |
| Square/Landscape | Label-Ausrichtung |
| Width (mm) | Label-Breite |
| Height (mm) | Label-Höhe |
| Rotation | Drehung (0, 90, 180, 270) |
| Custom Info | Zusatztext auf Label |

- **Test Print**: Testausdruck
- **Save**: Einstellungen speichern

### Tab: Backup & Restore

#### Backup erstellen
- Klick auf **"Backup herunterladen"**
- Erstellt eine komprimierte JSON-Datei (`.json.gz`)
- Enthält alle Projekte, Zellen, Batterien, Einstellungen

#### Backup wiederherstellen

⚠️ **Wichtig:** Vor dem Restore müssen die Datenbank-Tabellen existieren!

**Linux / macOS:**
```bash
# 1. Tabellen erstellen (falls neue Installation)
docker-compose exec web python manage.py migrate

# 2. Backup entpacken
gunzip megacnc_backup_XXXXXX.json.gz

# 3. Daten wiederherstellen
docker-compose exec web python manage.py loaddata megacnc_backup_XXXXXX.json
```

**Windows (PowerShell):**
```powershell
# 1. Tabellen erstellen (falls neue Installation)
docker exec megacnc-web-1 python manage.py migrate

# 2. Mit 7-Zip entpacken
7z e megacnc_backup_XXXXXX.json.gz

# 3. In Container kopieren und wiederherstellen
docker cp megacnc_backup_XXXXXX.json megacnc-web-1:/app/
docker exec megacnc-web-1 python manage.py loaddata megacnc_backup_XXXXXX.json
```

⚠️ **Achtung:** Ein Restore überschreibt alle aktuellen Daten!

---

## Workflow-Beispiel

### Zellen testen und Pack bauen

```
1. Projekt erstellen → "Samsung 30Q Batch 1"
2. Device hinzufügen → Projekt zuweisen
3. Zellen in Slots einlegen
4. Macro starten → Charge → Discharge → Store
5. Nach Abschluss: Zellen speichern (Disketten-Icon)
6. Labels drucken
7. Batteries → Neues Pack erstellen (z.B. 4S2P)
8. Zellen aus Projekt laden
9. Auto Select + Assign
10. Save Pack
```

---

## Tipps

### Gute Zellen-Matches für Parallel
- Ähnliche Kapazität (±50 mAh) → wird vom Algorithmus optimiert
- Ähnliche Spannung (±0.1V) → Store-Funktion vor Pack-Bau nutzen
- Ähnlicher ESR (±10 mΩ) → wird vom Algorithmus optimiert

### Projekt-Organisation
- Separates Projekt pro Zell-Charge
- Eindeutige Namen für Rückverfolgbarkeit

### Optimale Pack-Qualität
1. Kapazitätsbereich eng wählen (z.B. 2400-2600 mAh)
2. Auto Select für repräsentative Auswahl nutzen
3. Assign für automatisches Balancing
4. Console (F12) prüfen für Balancing-Statistik:
   - Capacity StdDev: < 10 mAh = sehr gut, < 1 mAh = perfekt
   - Resistance StdDev: < 0.5 mΩ = sehr gut, < 0.1 mΩ = perfekt

### Sicherheit
- Zellen vor Parallelschaltung auf gleiche Spannung bringen (Store-Funktion)
- Defekte Zellen (hoher ESR, niedrige Kapazität) aussortieren
- Temperaturlimits einhalten
- Bei Ersatz: Immer Zelle mit ähnlichen Werten verwenden

---

## 8. Deployment & Administration

### Docker Images zu GitHub Container Registry pushen

Das Script `deploy-ghcr.sh` automatisiert den Image-Push.

#### Voraussetzungen
1. GitHub Personal Access Token erstellen:
   - https://github.com/settings/tokens/new
   - Berechtigungen: `write:packages`, `read:packages`

2. Token als Umgebungsvariable setzen:
```bash
export GHCR_TOKEN="ghp_xxxxxxxxxxxx"
# Oder in ~/.bashrc für Persistenz
```

#### Verwendung
```bash
# Mit automatischer Versionsnummer (Datum)
./deploy-ghcr.sh

# Mit spezifischer Version
./deploy-ghcr.sh v1.0.0
```

#### Was das Script macht
1. Optional: Datenbank-Backup erstellen
2. Login bei ghcr.io
3. Docker Image bauen
4. Image taggen (Version + latest)
5. Push zu `ghcr.io/USERNAME/megacnc`

### Auf Produktionsserver deployen

```bash
# Image pullen
docker pull ghcr.io/USERNAME/megacnc:latest

# In docker-compose.yml ändern:
# Von: build: .
# Zu:  image: ghcr.io/USERNAME/megacnc:latest

# Container neustarten
docker-compose down
docker-compose up -d
```

### Datenbank migrieren (Dev → Prod)

1. **Backup auf Dev erstellen** (Settings → Backup & Restore)
2. **Backup-Datei auf Prod kopieren**
3. **Restore auf Prod ausführen** (siehe Backup & Restore Anleitung)
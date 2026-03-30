# Giga CN - Benutzerhandbuch

## Übersicht

Giga CN (Fork von MegaCell CNC) ist eine Webanwendung zur Verwaltung von Batteriezellen-Tests und Battery Pack-Konfiguration.

---

## 1. Dashboard (Home)

Die Startseite zeigt Kennzahlen, Projekt- und Geräteübersichten sowie (optional) eine Historie neuer Zellen.

### Kennzahlen (Karten)

| Karte | Bedeutung |
|-------|-----------|
| **Total Cells** | Anzahl aller in der Datenbank erfassten Zellen |
| **Good Cells** | Zellen mit Kapazität **über 1000 mAh** (technischer Filter in der App) |
| **Total Projects** | Anzahl der Projekte |
| **Available Cells** | Zellen mit **Available = Yes** (für Battery Packs nutzbar freigegeben) |

### Tabellen

- **Projects**: Übersicht aller Projekte (Name verlinkt die **Projekt-Details**, siehe Abschnitt 2).
- **Devices**: Übersicht aller registrierten Testgeräte (Name verlinkt die **Device Slots** des jeweiligen Geräts).

### Neue Zellen (letzte 2 Monate)

Bereich **„Neue Zellen (letzte 2 Monate)“** (ca. 62 Tage, nach **Einfügedatum** der Zelle):

- Gruppierung nach **Kalendertag** und **Projekt** mit Anzahl der neu erfassten Zellen.
- **Zeile anklicken**: Detailbereich klappt auf (nur eine Zeile gleichzeitig geöffnet). Es werden die zugehörigen Zellen wie in der Database-Ansicht gelistet; Link **Database** springt zum Projektfilter.
- Wenn im Zeitraum keine Zellen angelegt wurden, erscheint ein Hinweistext.

---

## 2. Projects

### Zweck
Projekte organisieren Zellen nach Herkunft oder Verwendungszweck (z.B. "Samsung 30Q Batch 1", "Recycling Laptop-Akkus").

### Funktionen
- **+ Add Project**: Neues Projekt erstellen
  - Project Name
  - Cell Type (18650, 21700, LifePo4, Other)
  - Notes
- In der **linken Sidebar** gibt es zusätzlich den Button **New Project** (gleiche Funktion wie „Projekt anlegen“, je nach Theme).

### Anzeige
| Spalte | Beschreibung |
|--------|-------------|
| Project Name | Name des Projekts (klickbar für Details) |
| Device Count | Anzahl zugewiesener Testgeräte |
| Creation Date | Erstellungsdatum |
| Notes | Notizen |
| Status | Active/Inactive |
| Total Cells | Anzahl getesteter Zellen |

### Projekt-Details (alle Geräte eines Projekts)

Über den **Projektnamen** in der Projects-Tabelle öffnet sich die Seite **Projekt-Details** (`project-details` mit `proj_id`).

| Aspekt | Beschreibung |
|--------|----------------|
| **Zweck** | Zentrale Ansicht für **alle Slots aller dem Projekt zugewiesenen Geräte** (eine gemeinsame Tabelle). |
| **Steuerung** | Gleiche Aktionen wie unter **Device Slots**: Charge, Discharge, Store, ESR, Dispose, Stop, Macro, Stop Macro, Print (siehe Abschnitt 4). |
| **Auswahl** | Checkboxen pro Slot; die Werte enthalten **Gerät und Slot** – die Oberfläche gruppiert beim Senden automatisch nach **Device**. |

**Mehrere Geräte parallel:** Wenn du Slots **auf verschiedenen Geräten** anwählst und z. B. **Charge** startest, sendet der Browser **pro Gerät einen eigenen Auftrag** an den Server. Die Befehle werden im Hintergrund (Celery) verarbeitet und können **parallel** ablaufen – jedes Gerät hat eine eigene IP. Details siehe Abschnitt 3.

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

### Mehrere Geräte gleichzeitig nutzen

| Frage | Antwort |
|-------|---------|
| **Wie arbeite ich mit mehreren Geräten?** | Jedes Gerät erscheint in der **Devices**-Liste. Pro Gerät öffnest du **Device Slots** (Klick auf den Namen) – dort steuerst du **nur dieses eine** Gerät. |
| **Wie starte ich Tests auf mehreren Geräten parallel?** | Am praktischsten über **Projekt-Details** (Abschnitt 2): dort alle gewünschten Slots über mehrere Geräte anhaken und die gewünschte Aktion wählen. Die App sendet **je Gerät einen Auftrag**; die Geräte arbeiten unabhängig parallel. |
| **Ein Gerät, viele Slots** | Unter **Device Slots** ein Gerät wählen, mehrere Slots anhaken, **eine** Aktion – ein Auftrag enthält alle gewählten Slots; die Hardware verarbeitet die Slots gemäss Geräte-Firmware. |
| **Garantierte Reihenfolge zwischen Geräten?** | Nein – es gibt keine zentrale „Start alles atomar“-Transaktion; Aufträge sind unabhängig voneinander. |

**Hintergrund (Kurz):** Jeder Klick löst serverseitig u. a. eine Hintergrundaufgabe aus; mehrere Worker können gleichzeitig verschiedene Geräte ansprechen. Statusmeldungen erscheinen pro Gerät (z. B. Toasts mit Geräte-ID).

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

> **Hinweis:** Aktionen auf **mehreren Geräten gleichzeitig** sind über **Projekt-Details** möglich (siehe Abschnitt 2 und 3), nicht über diese Einzelgeräte-Seite allein.

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

### Seitengröße (Pagination)

- Dropdown **„Zellen pro Seite“** (z. B. 50 / 100 / 250 / 500): steuert `per_page` und lädt per AJAX die nächste Seite, ohne die Filter zu verlieren.

### Kopfzeile: Export-Icon

- Neben den Filtern gibt es ein **Download-Icon** („Export Report“). In der aktuellen Anwendung ist dafür **kein Klick-Handler** im Frontend hinterlegt – der Button kann je nach Build ohne Funktion sein. Für eine tabellarische Auswertung kannst du die angezeigte Tabelle manuell kopieren oder auf einen späteren Export vertrauen.

### Zellen löschen

| Aktion | Beschreibung |
|--------|----------------|
| **Einzelzelle** | Papierkorb-Icon in der Zeile → Bestätigung → Zelle wird entfernt. |
| **Mehrfachauswahl** | Checkboxen links aktivieren → Papierkorb in der Kopfzeile wird aktiv → Massen-Löschen mit Bestätigung. |

⚠️ Gelöschte Zellen sind aus der Datenbank entfernt – Vorsicht bei Produktivdaten.

### Verlaufsgrafik (+ / Details)

- **+** in der Zeile öffnet erweiterte Messwerte und kann eine **Verlaufsgrafik** (Zeitreihe) laden (`/get-history/`), sofern Testdaten vorliegen.

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

Die Settings-Seite ist in **drei Tabs** organisiert: **Printer**, **Devices** (u. a. Beat-Intervall) und **Backup & Restore**. Weitere App-Einstellungen sind hier nicht zentral gebündelt.

### Tab: Printer

Konfiguriert den Labeldrucker (z.B. Dymo).

#### Label-Informationen

Jedes gedruckte Label enthält folgende Daten:

| Zeile | Beispiel | Beschreibung |
|-------|----------|-------------|
| **Header** | `005450-C:3245` | SerialNo (aus UUID) + Kapazität |
| **Einheit** | `mAh` | Kapazitäts-Einheit (mAh oder Ah bei ≥10'000) |
| **Zeile 1** | `I:0.1 T:25` | ESR (Innenwiderstand mΩ) + Max. Temperatur (°C) |
| **Zeile 2** | `2.8/3.7/4.24` | Min-Spannung / Store-Spannung / Max-Spannung (V) |
| **Zeile 3** | `Mc: 104-1` | Ladegerät-IP (letzte Zahl) - Slotnummer |
| **Datum** | `2024-02-23` | Einfügedatum der Zelle |
| **Custom** | `LabelPrinter-450` | Frei konfigurierbares Textfeld (aus Settings) |
| **QR-Code** | | Enthält: UUID + Kapazität + Einheit |
| **Branding** | `deepcyclepower.com` | Firmenname |

##### SerialNo

Die SerialNo wird aus der UUID der Zelle extrahiert (z.B. UUID `D20230620-S005450` → SerialNo `005450`).

##### Label-Modi

| Modus | Beschreibung |
|-------|-------------|
| **Square** | Einzellabel hochformat (13×25mm Dymo) |
| **Landscape** | Einzellabel querformat (30×20mm Phomemo) |
| **Dual Label** | Zwei Zellen auf einem Label (13×25mm Dymo) |

> **Hinweis:** Beim Dual-Label entfallen Datum und Custom-Feld aus Platzgründen.

#### Voraussetzung: QZ Tray

Zum Drucken von Labels wird **QZ Tray** benötigt. QZ Tray ist eine Desktop-Anwendung, die als Brücke zwischen dem Browser und den lokalen Druckern dient. Ohne QZ Tray kann der Browser nicht auf Drucker zugreifen.

**Download:** https://qz.io/download

##### Installation Linux

```bash
# Voraussetzung: Java (OpenJDK 11+)
sudo apt install openjdk-11-jre

# Installer herunterladen
curl -L -o /tmp/qz-tray.run \
  "https://github.com/qzind/tray/releases/latest/download/qz-tray-2.2.5-x86_64.run"

# Installieren
chmod +x /tmp/qz-tray.run
sudo /tmp/qz-tray.run

# Starten
/opt/qz-tray/qz-tray &
```

##### Installation macOS

1. `.pkg`-Datei von https://qz.io/download herunterladen
2. Doppelklick auf die `.pkg`-Datei
3. Installationsassistent folgen
4. QZ Tray startet automatisch (Tray-Icon in der Menüleiste)

##### Installation Windows

1. `.exe`-Datei von https://qz.io/download herunterladen
2. Doppelklick auf die `.exe`-Datei
3. Installationsassistent folgen
4. QZ Tray startet automatisch (Tray-Icon im Infobereich)

> **Hinweis:** QZ Tray muss auf dem PC laufen, auf dem der Browser geöffnet ist – nicht auf dem Server.

#### Step 1: Verbindung
1. QZ Tray starten (falls nicht bereits aktiv)
2. "Connect" klicken → Status wechselt auf "Active"
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

Hier verwaltest du **Datenbank-Backups** (JSON-Fixture, gzip) und siehst **Protokolle** sowie optional den **Migrations-Status**.

---

#### Backup erstellen

- Klick auf **„Backup herunterladen“**.
- Es wird eine komprimierte Datei **`.json.gz`** im Browser heruntergeladen (Inhalt: Projekte, Zellen, Batterien, Geräte, Drucker-Einstellungen u. a. – entspricht `dumpdata`).
- **Zusätzlich** legt die App eine **Kopie mit gleichem Dateinamen** im **Server-Archiv** ab (siehe unten), damit Backups auch ohne erneuten Download auf dem Server verfügbar sind.

---

#### Backup wiederherstellen (Datei vom eigenen Rechner)

Für ein Restore **ohne** Terminal:

1. Unter **„Backup wiederherstellen (Datei vom PC)“** eine Datei wählen: **`.json.gz`** (wie vom Download) oder entpacktes **`.json`**.
2. Checkbox bestätigen (Hinweis: **alle aktuellen Daten** werden durch die Datei ersetzt).
3. **„Aus Datei wiederherstellen“** klicken.

**Ablauf im Hintergrund:**

- Vor dem Einspielen wird ein **Sicherheits-Backup des aktuellen Stands** erzeugt und im Server-Archiv gespeichert, Dateiname z. B.  
  `sicherheit_vor_restore_YYYYMMDD_HHMMSS.json.gz`
- Anschließend wird die Datenbank geleert und die gewählte Datei eingespielt (`loaddata`).
- Bei Fehlern beim Einspielen versucht die App, den **vorherigen Stand** aus dem temporären Sicherheits-Dump wiederherzustellen.

**Hinweise:**

- Der Vorgang kann bei großen Datenmengen **mehrere Minuten** dauern; eine **Fortschrittsanzeige** erscheint währenddessen.
- Die Seite währenddessen **nicht schließen**.

⚠️ **Achtung:** Ein erfolgreicher Restore **ersetzt** die komplette Datenbank durch den Inhalt der Datei.

---

#### Backups auf dem Server

Die Tabelle listet alle **im Archiv liegenden** Dateien (nicht nur der Browser-Download).

| Aspekt | Beschreibung |
|--------|--------------|
| **Speicherort** | Konfigurierbar über Umgebungsvariable **`BACKUP_ARCHIVE_DIR`** (Standard unter dem Projekt `data/backups`; in Docker oft z. B. **`/data/backups`** auf dem Volume). |
| **Typ** | **Sicherheit (vor Restore)** – automatisch vor jedem Restore; **Manuell (Download)** – Kopie von „Backup herunterladen“. |
| **Aktionen** | **Herunterladen** (nochmal als Datei), **Einspielen** (Restore **direkt** aus dieser Server-Datei), **Checkboxen** zum Markieren. |
| **Ausgewählte löschen** | Entfernt markierte Dateien **nur** aus dem Archiv (nicht die laufende Datenbank). |

**Restore aus der Liste („Einspielen“):** Es öffnet sich ein Dialog mit Bestätigung; Ablauf wie oben inkl. neuem Sicherheits-Backup und Fortschrittsanzeige.

---

#### Journal (Backup / Restore)

Unterhalb der Archiv-Tabelle zeigt das **Journal** die letzten Ereignisse mit **Zeit (UTC)**, **Aktion**, **Von/Quelle**, **Nach/Ziel**, **Status** und **Details**.

Typische Einträge u. a.:

- manueller Backup-Download (Datenbank → Archiv + Browser),
- Restore von **Upload** oder **Server-Archiv** (inkl. Hinweis auf die erzeugte Sicherheitsdatei),
- Löschen von Archiv-Dateien,
- Download einer Archiv-Datei zum PC.

**„Journal aktualisieren“** lädt die Liste neu.

---

#### Datenbank-Schema (Migrationen)

- **Docker (empfohlen):** Beim **Start des Web-Containers** wird in der Regel automatisch **`python manage.py migrate --noinput`** ausgeführt, **bevor** der Webserver startet. Nach einem **Image-Update** und **Neustart** der Container werden neue Migrationen so angewendet – oft ist kein manuelles `migrate` nötig.
- Die Anzeige **„Keine ausstehenden Migrationen“** / Anzahl ausstehender Migrationen bezieht sich auf den aktuellen Datenbankstand.
- Optional (nur wenn der Administrator **`ALLOW_UI_MIGRATE=1`** setzt): Button **„Migration jetzt ausführen“** als **Fallback** – nicht parallel auf mehreren Instanzen unkontrolliert klicken.

**Ohne Docker** (lokale Entwicklung): virtuelle Umgebung, `pip install -r requirements.txt`, dann `python3 manage.py migrate` (unter Linux heißt der Befehl oft `python3`, nicht `python`).

---

#### Experten: Restore nur per Terminal (Docker)

Wenn du **keine** Weboberfläche nutzen willst, geht der Restore wie bisher mit `loaddata` im Container. **Wichtig:** Zuerst Migrationen / leere DB wie bei Neuinstallation.

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

⚠️ **Achtung:** Ein Restore überschreibt alle aktuellen Daten in der Datenbank!

---

## Workflow-Beispiel

### Zellen testen und Pack bauen

```
1. Projekt erstellen → "Samsung 30Q Batch 1"
2. Device(s) hinzufügen → Projekt zuweisen (mehrere Geräte möglich)
3. Zellen in Slots einlegen
4. Tests starten:
   - nur ein Gerät: Device Slots → Macro / Charge …
   - mehrere Geräte: Projects → Projektnamen klicken → Projekt-Details → Slots wählen → Aktion
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

### Mehrere Ladegeräte
- **Projekt-Details** nutzen, wenn du dieselbe Aktion auf **mehreren IPs** gleichzeitig anstoßen willst (siehe Abschnitt 2 und 3).
- Celery-Logs mit `check_all_devices` alle paar Sekunden sind normal (Statusabfrage der Geräte).

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

Das Script `scripts/deploy-ghcr.sh` automatisiert den Image-Push.

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
./scripts/deploy-ghcr.sh

# Mit spezifischer Version
./scripts/deploy-ghcr.sh v1.0.0
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

1. **Backup auf Dev erstellen** (Settings → Backup & Restore → „Backup herunterladen“; optional die Archiv-Kopie auf dem Server prüfen).
2. **Auf Prod wiederherstellen**, z. B.:
   - **Datei auf den Admin-PC kopieren** und unter **Backup wiederherstellen (Datei vom PC)** einspielen, **oder**
   - Datei ins **Server-Archiv** legen (gleicher Pfad wie `BACKUP_ARCHIVE_DIR`) und in der Tabelle **„Einspielen“** wählen, **oder**
   - klassisch per **Terminal** (`loaddata`, siehe Abschnitt „Experten“).
3. Nach Image-Update auf Prod: Container neu starten, damit **`migrate`** beim Start läuft (Schema passt zum Backup-Inhalt).
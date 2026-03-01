# SQLite zu PostgreSQL Migration Guide

## Übersicht

Das Script `migrate_sqlite_to_postgres.py` migriert automatisch Daten von einer alten SQLite-Datenbank zur neuen PostgreSQL-Datenbank.

## Voraussetzungen

1. PostgreSQL-Datenbank ist eingerichtet und Migrationen sind ausgeführt
2. SQLite-Datenbank-Datei ist verfügbar
3. Django-Umgebung ist konfiguriert

## Verwendung

### Schritt 1: SQLite-DB vorhanden prüfen

Die SQLite-DB muss als `MegaCellMonitor.sqlite` im Hauptverzeichnis liegen oder über SQLITE_DB_PATH konfiguriert sein:

```python
SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', "/data/MegaCellMonitor.sqlite")
```

### Schritt 2: Script ausführen

**WICHTIG:** Das Script löscht ALLE vorhandenen Daten in megacellcnc_cells und megacellcnc_projects!

**Im Docker-Container:**
```bash
docker-compose exec web python migrate_sqlite_to_postgres.py
```

Das Script wird:
1. **TRUNCATE** auf megacellcnc_cells und megacellcnc_projects ausführen
2. **Projects** automatisch aus ProjectName erstellen
3. **Alle 20k+ Zellen** aus CellLibrary migrieren
4. **UUIDs** im Format D{LogDate:YYYYMMDD}-S{SerialNummer:06d} generieren

### Schritt 3: Migration bestätigen

Das Script zeigt:
1. Gefundene SQLite-Tabellen
2. Automatisches Mapping (SQLite → PostgreSQL)
3. Spalten-Mapping
4. Fragt nach Bestätigung

Nach Bestätigung startet die Migration.

## Was das Script macht

1. **Analysiert SQLite-DB:**
   - Findet alle Tabellen
   - Analysiert Spalten und Datentypen
   - Zählt Zeilen

2. **Erstellt automatisches Mapping:**
   - Vergleicht SQLite- mit PostgreSQL-Struktur
   - Findet passende Tabellen (auch bei unterschiedlichen Namen)
   - Mappt Spalten automatisch

3. **Migriert Daten:**
   - Migriert in richtiger Reihenfolge (Foreign Keys beachten)
   - Mappt Foreign Key IDs automatisch
   - Behandelt NULL-Werte korrekt
   - Überspringt Duplikate (ON CONFLICT DO NOTHING)

## Migration-Reihenfolge

**NUR CellLibrary Migration:**

Die Migration erfolgt in dieser Reihenfolge:

1. **TRUNCATE** megacellcnc_cells CASCADE
2. **TRUNCATE** megacellcnc_projects CASCADE
3. `megacellcnc_projects` (automatisch aus ProjectName erstellt)
4. `megacellcnc_cells` (CellLibrary -> megacellcnc_cells, ALLE 20k+ Einträge)

**Feld-Mapping CellLibrary → megacellcnc_cells:**
- `CellSerialNumber` + `LogDate` → `UUID` (D{YYYYMMDD}-S{NNNNNN})
- `ProjectName` → `project_id` (via Auto-Create)
- `Available` (bit 0/1) → `available` ("Yes"/"No")
- `capacity`, `voltage`, `esr`, `esr_ac` → direkt
- `temperature` → `temp_before_test`
- `discharge_cycles` → `cycles_count`
- `action_length` → `test_duration`
- Fehlende Felder bekommen Defaults (z.B. device_mac="00:00:00:00:00:00")

## Troubleshooting

### SQLite-DB nicht gefunden
```
❌ Fehler: SQLite-DB nicht gefunden
```
**Lösung:** Pfad in `SQLITE_DB_PATH` korrigieren

### Foreign Key Fehler
```
⚠ Fehler bei Zeile: foreign key constraint failed
```
**Lösung:** Script migriert automatisch in richtiger Reihenfolge. Falls Fehler auftreten, prüfe ob alle Tabellen gemappt wurden.

### Spalten nicht gefunden
```
⚠ Keine passende SQLite-Tabelle für megacellcnc_xxx
```
**Lösung:** Tabelle existiert nicht in SQLite-DB oder Name ist zu unterschiedlich. Prüfe manuell.

### Duplikate
Das Script verwendet `ON CONFLICT DO NOTHING`, daher werden Duplikate automatisch übersprungen.

## Nach der Migration

1. **Daten prüfen:**
   ```bash
   docker-compose exec web python manage.py shell
   ```
   
   ```python
   from megacellcnc.models import Projects, Cells
   
   # Anzahl prüfen
   print(f"Projects: {Projects.objects.count()}")
   print(f"Cells: {Cells.objects.count()}")
   
   # Projects anzeigen
   for p in Projects.objects.all():
       print(f"  - {p.Name}: {p.cells.count()} Zellen")
   
   # Verfügbare Zellen prüfen
   print(f"Verfügbare Zellen: {Cells.objects.filter(available='Yes').count()}")
   
   # UUID Format prüfen
   sample = Cells.objects.first()
   print(f"Beispiel UUID: {sample.UUID}")
   print(f"  Format: D{{YYYYMMDD}}-S{{NNNNNN}}")
   ```

2. **Erwartetes Ergebnis:**
   - **Cells:** 20.461 (alle aus CellLibrary)
   - **Projects:** 2+ (abhängig von eindeutigen ProjectNames)
   - **UUIDs:** Format D20220829-S000349 (Datum aus LogDate)
   - **Available:** "Yes" oder "No"

3. **Backup erstellen:**
   ```bash
   ./update-safe.sh  # Erstellt Backup der PostgreSQL-DB
   ```

## Manuelle Anpassungen

Falls das automatische Mapping nicht funktioniert, kannst du das Script anpassen:

1. **Tabellen-Mapping manuell setzen:**
   ```python
   # In AutoMapper._find_matching_table()
   manual_mapping = {
       'megacellcnc_projects': 'alte_tabellen_name',
   }
   ```

2. **Spalten-Mapping manuell setzen:**
   ```python
   # In AutoMapper._map_columns()
   manual_cols = {
       'Name': 'name',  # PostgreSQL <- SQLite
   }
   ```

## Wichtige Hinweise

- ⚠️ **Backup erstellen** vor Migration!
- ⚠️ Migration läuft in einer Transaktion (bei Fehler: Rollback)
- ⚠️ Duplikate werden übersprungen (keine doppelten Daten)
- ⚠️ Foreign Keys werden automatisch gemappt (alte ID → neue ID)

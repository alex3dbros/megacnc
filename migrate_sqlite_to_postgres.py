#!/usr/bin/env python3
"""
Automatische SQLite zu PostgreSQL Migration
- Analysiert SQLite-DB automatisch
- Erstellt automatischen Mapper
- Migriert Daten nach PostgreSQL
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
import re
from collections import defaultdict
from datetime import datetime, timedelta
import logging
import uuid as uuid_lib

# Django Models importieren (für PostgreSQL-Struktur)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')

import django
django.setup()

from django.db import connection as django_connection
from megacellcnc.models import (
    Projects, Device, Slot, Cells, CellTestData, 
    Chemistry, Batteries, PrinterSettings
)

# Konfiguration
# Pfad im Container: /data/MegaCellMonitor.sqlite (gemountet von /home/heinz/Dokumente/megacell/test)
SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', "/data/MegaCellMonitor.sqlite")
LOG_FILE = os.path.join(os.path.dirname(__file__), "migration_errors.log")

# Logging konfigurieren
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stderr)
    ]
)

class SQLiteAnalyzer:
    """Analysiert SQLite-Datenbankstruktur"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.tables = {}
        self.foreign_keys = {}
        
    def analyze(self):
        """Analysiert die komplette Datenbank"""
        print("=== Analysiere SQLite-Datenbank ===\n")
        
        # Alle Tabellen finden
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        table_names = [row[0] for row in cursor.fetchall()]
        
        print(f"Gefundene Tabellen: {', '.join(table_names)}\n")
        
        # Jede Tabelle analysieren
        for table_name in table_names:
            self.tables[table_name] = self._analyze_table(table_name)
        
        # Foreign Keys analysieren
        self._analyze_foreign_keys()
        
        return self.tables
    
    def _analyze_table(self, table_name):
        """Analysiert eine einzelne Tabelle"""
        cursor = self.conn.cursor()
        
        # Spalten-Informationen
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = {}
        for col in cursor.fetchall():
            col_id, name, col_type, not_null, default_val, pk = col
            columns[name] = {
                'type': col_type,
                'not_null': not_null,
                'default': default_val,
                'primary_key': pk
            }
        
        # Anzahl Zeilen
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Beispiel-Daten (erste Zeile)
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        sample = cursor.fetchone()
        sample_data = {}
        if sample:
            col_names = [desc[0] for desc in cursor.description]
            for i, val in enumerate(sample):
                sample_data[col_names[i]] = val
        
        return {
            'columns': columns,
            'row_count': row_count,
            'sample': sample_data
        }
    
    def _analyze_foreign_keys(self):
        """Analysiert Foreign Key Beziehungen"""
        cursor = self.conn.cursor()
        for table_name in self.tables.keys():
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            fks = cursor.fetchall()
            if fks:
                self.foreign_keys[table_name] = fks
    
    def get_data(self, table_name):
        """Holt alle Daten einer Tabelle"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return columns, rows
    
    def close(self):
        self.conn.close()


class AutoMapper:
    """Erstellt automatisch Mapper zwischen SQLite und PostgreSQL"""
    
    # Django Model -> Tabellenname Mapping
    MODEL_TO_TABLE = {
        'Projects': 'megacellcnc_projects',
        'Device': 'megacellcnc_device',
        'Slot': 'megacellcnc_slot',
        'Cells': 'megacellcnc_cells',
        'CellTestData': 'megacellcnc_celltestdata',
        'Chemistry': 'megacellcnc_chemistry',
        'Batteries': 'megacellcnc_batteries',
        'PrinterSettings': 'megacellcnc_printersettings',
    }
    
    def __init__(self, sqlite_tables):
        self.sqlite_tables = sqlite_tables
        self.mapping = {}
        self.column_mapping = {}
        
    def create_mapping(self):
        """Erstellt automatisches Mapping"""
        print("\n=== Erstelle automatisches Mapping ===\n")
        
        # PostgreSQL Tabellen-Struktur holen
        pg_tables = self._get_postgres_tables()
        
        # Für jede PostgreSQL-Tabelle passende SQLite-Tabelle finden
        for pg_table, pg_columns in pg_tables.items():
            sqlite_table = self._find_matching_table(pg_table, pg_columns)
            if sqlite_table:
                self.mapping[pg_table] = sqlite_table
                # Spalten-Mapping erstellen
                self.column_mapping[pg_table] = self._map_columns(
                    sqlite_table, pg_columns
                )
                print(f"✓ {sqlite_table} -> {pg_table}")
            else:
                print(f"⚠ Keine passende SQLite-Tabelle für {pg_table}")
        
        return self.mapping, self.column_mapping
    
    def _get_postgres_tables(self):
        """Holt PostgreSQL Tabellen-Struktur"""
        with django_connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'megacellcnc_%'
                ORDER BY table_name
            """)
            tables = {}
            for row in cursor.fetchall():
                table_name = row[0]
                # Spalten holen
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, [table_name])
                columns = {col[0]: {'type': col[1], 'nullable': col[2] == 'YES'} 
                          for col in cursor.fetchall()}
                tables[table_name] = columns
            return tables
    
    def _find_matching_table(self, pg_table, pg_columns):
        """Findet passende SQLite-Tabelle durch Namens-Ähnlichkeit"""
        # Manuelle Mappings für spezielle Fälle
        manual_mapping = {
            'megacellcnc_cells': 'CellLibrary',
        }
        
        # Nur diese Tabellen matchen
        if pg_table in manual_mapping:
            sqlite_table = manual_mapping[pg_table]
            if sqlite_table in self.sqlite_tables:
                return sqlite_table
        
        # Für alle anderen Tabellen: Wenn CellLibrary die einzige verfügbare ist, NICHT matchen
        if list(self.sqlite_tables.keys()) == ['CellLibrary']:
            # Nur CellLibrary verfügbar - nicht zu anderen Tabellen matchen
            if pg_table not in manual_mapping:
                return None
        
        # Direkter Match
        if pg_table in self.sqlite_tables:
            return pg_table
        
        # Ähnliche Namen finden
        pg_name_clean = pg_table.replace('megacellcnc_', '').lower()
        best_match = None
        best_score = 0
        
        for sqlite_table in self.sqlite_tables.keys():
            sqlite_name_clean = sqlite_table.replace('megacellcnc_', '').lower()
            
            # Score basierend auf Namens-Ähnlichkeit
            score = self._similarity_score(pg_name_clean, sqlite_name_clean)
            
            # Zusätzlicher Score für Spalten-Übereinstimmung
            sqlite_cols = set(self.sqlite_tables[sqlite_table]['columns'].keys())
            pg_cols = set(pg_columns.keys())
            common_cols = len(sqlite_cols & pg_cols)
            score += common_cols * 0.1
            
            if score > best_score:
                best_score = score
                best_match = sqlite_table
        
        return best_match if best_score > 0.5 else None
    
    def _similarity_score(self, str1, str2):
        """Berechnet Ähnlichkeits-Score zwischen zwei Strings"""
        if str1 == str2:
            return 1.0
        if str1 in str2 or str2 in str1:
            return 0.8
        # Levenshtein-ähnlich (vereinfacht)
        common_chars = len(set(str1) & set(str2))
        return common_chars / max(len(str1), len(str2)) if max(len(str1), len(str2)) > 0 else 0
    
    def _map_columns(self, sqlite_table, pg_columns):
        """Mappt Spalten zwischen SQLite und PostgreSQL"""
        sqlite_cols = self.sqlite_tables[sqlite_table]['columns']
        mapping = {}
        
        # Spezielle Mappings für bestimmte Tabellen
        special_mappings = {
            'megacellcnc_chemistry': {
                'store_Voltage': ['store_voltage', 'StoreVoltage', 'store_Voltage', 'Store_Voltage'],
            },
            'CellLibrary': {
                # Manuelle Spalten-Mappings für CellLibrary -> megacellcnc_cells
                # WICHTIG: Leere Strings statt None für spezielle Felder!
                'UUID': '',  # Wird generiert (leerer String damit es nicht übersprungen wird)
                'project_id': '',  # Via ProjectName Lookup (leerer String)
                'available': '',  # Wird konvertiert (leerer String)
                'capacity': 'capacity',
                'voltage': 'voltage',
                'esr': 'esr',
                'esr_ac': 'esr_ac',
                'min_voltage': 'min_voltage',
                'max_voltage': 'max_voltage',
                'store_voltage': 'store_voltage',
                'temp_before_test': 'temperature',
                'cycles_count': 'discharge_cycles',
                'test_duration': 'action_length',
                'insertion_date': 'LogDate',
                'cell_type': 'CellType',
                'device_ip': 'charger_icc',
                'device_slot': 'CCiD',
                'device_mac': '',  # Default (leerer String)
                'device_type': 'charger_type',
                'charge_duration': '',  # Default 0.0 (leerer String)
                'discharge_duration': '',  # Default 0.0 (leerer String)
                'avg_temp_charging': '',  # Default 0 (leerer String)
                'avg_temp_discharging': '',  # Default 0 (leerer String)
                'max_temp_charging': '',  # Default 0 (leerer String)
                'max_temp_discharging': '',  # Default 0 (leerer String)
                'testing_current': '',  # Default 0 (leerer String)
                'discharge_mode': '',  # Default 'CC' (leerer String)
                'status': '',  # Default 'Completed' (leerer String)
                'bat_position': '',  # Default '' (leerer String)
                'battery_id': '',  # Default NULL (leerer String, wird zu None)
                'removal_date': '',  # Default NULL (leerer String, wird zu None)
            }
        }
        
        # Wenn es ein spezielles Table-Mapping gibt, verwende es KOMPLETT
        if sqlite_table in special_mappings:
            # Verwende nur das spezielle Mapping, kein Auto-Mapping
            return special_mappings[sqlite_table]
        
        for pg_col in pg_columns.keys():
            # Spezielle Mappings prüfen
            table_name = None
            for table in special_mappings:
                if table in pg_columns:
                    table_name = table
                    break
            
            if table_name and pg_col in special_mappings.get(table_name, {}):
                # Versuche spezielle Mappings
                found = False
                for sqlite_col in special_mappings[table_name][pg_col]:
                    if sqlite_col in sqlite_cols:
                        mapping[pg_col] = sqlite_col
                        found = True
                        break
                if found:
                    continue
            
            # Direkter Match (case-insensitive)
            if pg_col in sqlite_cols:
                mapping[pg_col] = pg_col
            else:
                # Case-insensitive Match
                pg_col_lower = pg_col.lower()
                direct_match = None
                for sqlite_col in sqlite_cols.keys():
                    if sqlite_col.lower() == pg_col_lower:
                        direct_match = sqlite_col
                        break
                
                if direct_match:
                    mapping[pg_col] = direct_match
                else:
                    # Ähnliche Namen finden
                    best_match = None
                    best_score = 0
                    for sqlite_col in sqlite_cols.keys():
                        score = self._similarity_score(pg_col.lower(), sqlite_col.lower())
                        if score > best_score:
                            best_score = score
                            best_match = sqlite_col
                    
                    if best_score > 0.6:
                        mapping[pg_col] = best_match
                    else:
                        mapping[pg_col] = None  # Kein Match gefunden
        
        return mapping


class DataMigrator:
    """Migriert Daten von SQLite nach PostgreSQL"""
    
    # Migration-Reihenfolge (Foreign Keys beachten!)
    # Nur Projects und Cells für CellLibrary Migration
    MIGRATION_ORDER = [
        'megacellcnc_projects',
        'megacellcnc_cells',
    ]
    
    # Datumsspalten (werden automatisch konvertiert)
    DATE_COLUMNS = [
        'creation_date', 'insertion_date', 'removal_date', 'timestamp', 
        'insert_date', 'CreationDate', 'created_at', 'updated_at'
    ]
    
    def __init__(self, sqlite_analyzer, mapper):
        self.sqlite_analyzer = sqlite_analyzer
        self.mapper = mapper
        self.id_mapping = defaultdict(dict)  # Alte ID -> Neue ID Mapping
        self.pg_date_columns = {}  # Cache für Datumsspalten pro Tabelle
        self.project_cache = {}  # Cache für Projects (ProjectName -> project_id)
    
    def _truncate_tables(self):
        """Leert Ziel-Tabellen vor Migration"""
        print("\n=== Leere Ziel-Tabellen ===\n")
        with django_connection.cursor() as cursor:
            # Cells zuerst (wegen Foreign Key zu Projects)
            cursor.execute("TRUNCATE TABLE megacellcnc_cells CASCADE;")
            print("  ✓ megacellcnc_cells geleert")
            
            cursor.execute("TRUNCATE TABLE megacellcnc_projects CASCADE;")
            print("  ✓ megacellcnc_projects geleert")
            
            django_connection.commit()
    
    def _ensure_project(self, project_name):
        """Erstellt Project falls nicht vorhanden, gibt project_id zurück"""
        if not project_name or project_name.strip() == '':
            project_name = 'Importierte Zellen'
        
        # Cache prüfen
        if project_name in self.project_cache:
            return self.project_cache[project_name]
        
        # Prüfe ob Project existiert oder erstelle es
        project, created = Projects.objects.get_or_create(
            Name=project_name,
            defaults={
                'CellType': 'not specified',
                'Notes': 'Automatisch importiert aus SQLite',
                'LastCellNumber': 0,
                'Status': 'Active',
                'TotalCells': 0,
                'DevCnt': 0
            }
        )
        
        self.project_cache[project_name] = project.id
        if created:
            print(f"  ✓ Project '{project_name}' erstellt (ID: {project.id})")
        
        return project.id
    
    def _convert_available(self, value):
        """Konvertiert SQLite bit → PostgreSQL string"""
        if value == 1:
            return 'Yes'
        elif value == 0:
            return 'No'
        else:  # NULL
            return 'Yes'
    
    def migrate(self):
        """Führt die Migration durch"""
        # Tabellen leeren VOR Migration
        self._truncate_tables()
        
        print("\n=== Starte Daten-Migration ===\n")
        
        for pg_table in self.MIGRATION_ORDER:
            if pg_table in self.mapper.mapping:
                sqlite_table = self.mapper.mapping[pg_table]
                self._migrate_table(pg_table, sqlite_table)
            else:
                print(f"⚠ Überspringe {pg_table} (kein Mapping)")
    
    def _get_date_columns(self, pg_table):
        """Ermittelt Datumsspalten für eine Tabelle"""
        if pg_table in self.pg_date_columns:
            return self.pg_date_columns[pg_table]
        
        with django_connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = %s
                AND (data_type LIKE '%%timestamp%%' OR data_type LIKE '%%date%%')
            """, [pg_table])
            date_cols = {row[0]: row[1] for row in cursor.fetchall()}
            self.pg_date_columns[pg_table] = date_cols
            return date_cols
    
    def _convert_datetime(self, value, column_name):
        """Konvertiert SQLite Datumswert zu PostgreSQL TIMESTAMP"""
        if value is None or value == '':
            return None
        
        # Wenn bereits String/DateTime, direkt zurückgeben
        if isinstance(value, str):
            try:
                # Versuche verschiedene Datumsformate zu parsen
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d']:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
            except:
                pass
        
        if isinstance(value, (datetime,)):
            return value
        
        # SQLite speichert als Integer (Unix Timestamp) oder Real (Julian Day)
        if isinstance(value, (int, float)):
            try:
                # Versuche als Unix Timestamp (Sekunden seit 1970)
                if value > 0:
                    # Prüfe ob es ein Unix Timestamp ist (typisch > 1000000000)
                    if value > 1000000000:
                        # Unix Timestamp in Sekunden
                        return datetime.fromtimestamp(value)
                    elif value > 1000000000000:
                        # Unix Timestamp in Millisekunden
                        return datetime.fromtimestamp(value / 1000)
                    else:
                        # Möglicherweise Julian Day (SQLite Format)
                        # Julian Day 2440587.5 = 1970-01-01
                        julian_day_epoch = 2440587.5
                        days = value - julian_day_epoch
                        try:
                            result = datetime(1970, 1, 1) + timedelta(days=days)
                            # Prüfe auf gültigen Datumsbereich
                            if result.year < 1900 or result.year > 2100:
                                return None
                            return result
                        except (OverflowError, ValueError):
                            return None
            except (ValueError, OSError, OverflowError):
                # Falls Konvertierung fehlschlägt, None zurückgeben
                return None
        
        return None
    
    def _generate_uuid(self, row_dict, pg_table):
        """Generiert UUID für Zellen wenn fehlend"""
        if pg_table == 'megacellcnc_cells':
            # Versuche UUID aus CellSerialNumber und LogDate zu generieren
            cell_serial = row_dict.get('CellSerialNumber')
            log_date = row_dict.get('LogDate')
            
            if cell_serial and log_date:
                # Parse LogDate und formatiere als D{YYYYMMDD}
                date_obj = self._convert_datetime(log_date, 'LogDate')
                if date_obj:
                    date_str = date_obj.strftime('%Y%m%d')
                else:
                    # Fallback auf aktuelles Datum wenn Parsing fehlschlägt
                    date_str = datetime.now().strftime('%Y%m%d')
                return f"D{date_str}-S{int(cell_serial):06d}"
            elif cell_serial:
                # Nur SerialNumber ohne LogDate
                date_str = datetime.now().strftime('%Y%m%d')
                return f"D{date_str}-S{int(cell_serial):06d}"
            # Fallback: UUID generieren
            return f"MIGRATED-{uuid_lib.uuid4().hex[:12].upper()}"
        elif pg_table == 'megacellcnc_batteries':
            # Batterie UUID generieren
            date_str = datetime.now().strftime('%Y%m%d')
            return f"B{date_str}-{uuid_lib.uuid4().hex[:8].upper()}"
        return None
    
    def _get_required_columns(self, pg_table):
        """Ermittelt Pflichtfelder (NOT NULL ohne Default)"""
        with django_connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
                AND is_nullable = 'NO'
                AND column_default IS NULL
                AND column_name != 'id'
            """, [pg_table])
            return [row[0] for row in cursor.fetchall()]
    
    def _migrate_table(self, pg_table, sqlite_table):
        """Migriert eine einzelne Tabelle"""
        print(f"\nMigriere {sqlite_table} -> {pg_table}...")
        
        # Daten aus SQLite holen
        columns, rows = self.sqlite_analyzer.get_data(sqlite_table)
        if not rows:
            print(f"  Keine Daten in {sqlite_table}")
            return
        
        # Spalten-Mapping
        col_mapping = self.mapper.column_mapping[pg_table]
        
        # Tatsächliche PostgreSQL-Spalten ermitteln (mit exakter Schreibweise)
        with django_connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, [pg_table])
            actual_pg_columns = {row[0]: row[0] for row in cursor.fetchall()}  # Dict: lowercased -> actual name
        
        # Pflichtfelder ermitteln
        required_columns = self._get_required_columns(pg_table)
        
        # Korrigiere Mapping-Schlüssel auf tatsächliche Spaltennamen
        corrected_col_mapping = {}
        for col_key, sqlite_col in col_mapping.items():
            # Finde die exakte Schreibweise der PostgreSQL-Spalte
            actual_col = actual_pg_columns.get(col_key)
            if actual_col:
                corrected_col_mapping[actual_col] = sqlite_col
            else:
                # Case-insensitive Match
                found = False
                for actual_name in actual_pg_columns.values():
                    if actual_name.lower() == col_key.lower():
                        corrected_col_mapping[actual_name] = sqlite_col
                        found = True
                        break
                # Wenn nicht gefunden, behalte Original (kann None sein)
                if not found:
                    corrected_col_mapping[col_key] = sqlite_col
        
        col_mapping = corrected_col_mapping
        
        # PostgreSQL Spalten - nur die, die tatsächlich existieren
        pg_columns = [col for col in col_mapping.keys()]
        # Nur Spalten mit Mapping verwenden ODER Pflichtfelder (für Defaults)
        pg_columns = [col for col in pg_columns if col_mapping.get(col) is not None or col in required_columns]
        
        # Für Pflichtfelder ohne Mapping: Mapping auf None setzen (wird später behandelt)
        for col in required_columns:
            if col not in col_mapping and col in actual_pg_columns.values():
                col_mapping[col] = None
                if col not in pg_columns:
                    pg_columns.append(col)
        
        # Datumsspalten ermitteln
        date_columns = self._get_date_columns(pg_table)
        
        # Foreign Key Spalten identifizieren
        fk_columns = [col for col in pg_columns if col.endswith('_id')]
        
        # ID-Spalte finden
        id_col_sqlite = 'id' if 'id' in columns else None
        
        with django_connection.cursor() as cursor:
            migrated_count = 0
            skipped_count = 0
            for row in rows:
                # Daten mappen
                row_dict = dict(zip(columns, row))
                values = []
                pg_cols_clean = []
                skip_row = False
                
                # SPEZIELLE LOGIK FÜR CellLibrary Migration
                if sqlite_table == 'CellLibrary' and pg_table == 'megacellcnc_cells':
                    # 1. Project ermitteln/erstellen via ProjectName
                    project_name = row_dict.get('ProjectName', '')
                    project_id = self._ensure_project(project_name)
                    # In row_dict speichern für spätere Verwendung
                    row_dict['_project_id'] = project_id
                    
                    # 2. UUID generieren
                    uuid = self._generate_uuid(row_dict, pg_table)
                    row_dict['_uuid'] = uuid
                    
                    # 3. Available konvertieren
                    available_val = row_dict.get('Available')
                    row_dict['_available'] = self._convert_available(available_val)
                    
                    # DEBUG für erste Zeile
                    if migrated_count == 0 and skipped_count == 0:
                        print(f"\n  DEBUG: Erste Zeile CellSerialNumber={row_dict.get('CellSerialNumber')}")
                        print(f"  DEBUG: project_id={project_id}, uuid={uuid}, available={row_dict['_available']}")
                        print(f"  DEBUG: pg_columns hat {len(pg_columns)} Spalten")
                        print(f"  DEBUG: Erste 5 pg_columns: {pg_columns[:5]}")
                        print(f"  DEBUG: 'UUID' in pg_columns: {'UUID' in pg_columns}")
                        print(f"  DEBUG: 'project_id' in pg_columns: {'project_id' in pg_columns}")
                
                for pg_col in pg_columns:
                    sqlite_col = col_mapping.get(pg_col) if pg_col in col_mapping else None
                    # Leere Strings als "kein Mapping" behandeln
                    if sqlite_col == '':
                        sqlite_col = None
                    value = None
                    
                    # Spezielle Werte aus CellLibrary Pre-Processing
                    if sqlite_table == 'CellLibrary' and pg_table == 'megacellcnc_cells':
                        if pg_col == 'project_id':
                            value = row_dict.get('_project_id')
                        elif pg_col == 'UUID':
                            value = row_dict.get('_uuid')
                        elif pg_col == 'available':
                            value = row_dict.get('_available')
                        elif pg_col == 'cell_type':
                            # Immer auf 18650 setzen (aktuell nur dieser Type verwendet)
                            value = '18650'
                        elif pg_col == 'device_ip':
                            # Versuche aus charger_icc zu holen, sonst Default
                            value = row_dict.get('charger_icc', '192.168.1.33')
                        elif pg_col == 'device_slot':
                            # Aus CCiD holen
                            value = row_dict.get('CCiD', 0)
                        elif pg_col == 'device_mac':
                            value = '00:00:00:00:00:00'
                        elif pg_col == 'device_type':
                            value = row_dict.get('charger_type', 'Unknown')
                        elif pg_col == 'charge_duration':
                            value = 0.0
                        elif pg_col == 'discharge_duration':
                            value = 0.0
                        elif pg_col == 'avg_temp_charging':
                            value = 0
                        elif pg_col == 'avg_temp_discharging':
                            value = 0
                        elif pg_col == 'max_temp_charging':
                            value = 0
                        elif pg_col == 'max_temp_discharging':
                            value = 0
                        elif pg_col == 'testing_current':
                            value = 0
                        elif pg_col == 'discharge_mode':
                            value = 'CC'
                        elif pg_col == 'status':
                            value = 'Completed'
                        elif pg_col == 'bat_position':
                            value = ''
                        elif pg_col == 'battery_id':
                            value = None
                        elif pg_col == 'removal_date':
                            value = None
                        
                        # Prüfen ob diese Spalte speziell behandelt wurde
                        # NUR die Spalten, die tatsächlich oben behandelt werden!
                        was_handled = pg_col in ['UUID', 'project_id', 'available', 'cell_type', 'device_ip', 
                                                  'device_slot', 'device_mac', 'device_type', 
                                                  'charge_duration', 'discharge_duration', 'avg_temp_charging', 
                                                  'avg_temp_discharging', 'max_temp_charging', 'max_temp_discharging', 
                                                  'testing_current', 'discharge_mode', 'status', 'bat_position', 
                                                  'battery_id', 'removal_date']
                        
                        # WICHTIG: Wenn Spalte speziell behandelt wurde, zu values hinzufügen und continue
                        if was_handled:
                            # Direkt zu values hinzufügen und zur nächsten Spalte
                            if migrated_count == 0 and skipped_count == 0 and len(values) < 3:
                                print(f"    DEBUG: Spalte '{pg_col}' -> Wert '{value}' (speziell)")
                            values.append(value)
                            pg_cols_clean.append(pg_col)
                            continue
                    
                    # Wert aus SQLite holen (nur wenn noch nicht durch spezielle Logik gesetzt)
                    if sqlite_col and sqlite_col in row_dict:
                        value = row_dict[sqlite_col]
                        if migrated_count == 0 and skipped_count == 0 and len(values) < 5:
                            print(f"    DEBUG: Spalte '{pg_col}' <- '{sqlite_col}' = '{str(value)[:20]}...' (aus SQLite)")
                    
                    # slot_number speziell behandeln (vor anderen Checks)
                    if pg_col == 'slot_number':
                        # Immer versuchen, slot_number zu setzen, auch wenn kein Mapping existiert
                        if value is None or value == '':
                            # Versuche verschiedene Quellen
                            cell_id = row_dict.get('cell_id')
                            charger_cell_id = row_dict.get('ChargerCell_id') or row_dict.get('CCiD')
                            
                            # Bevorzuge cell_id (scheint die Slot-Nummer zu sein)
                            if cell_id:
                                try:
                                    value = int(cell_id)
                                except (ValueError, TypeError):
                                    pass
                            
                            # Fallback: ChargerCell_id
                            if value is None and charger_cell_id:
                                try:
                                    # ChargerCell_id könnte die Slot-Nummer sein (z.B. 116 -> 16)
                                    charger_val = int(charger_cell_id)
                                    # Versuche letzte 2 Ziffern
                                    value = charger_val % 100
                                    if value == 0:
                                        # Oder letzte Ziffer
                                        value = charger_val % 10
                                    if value == 0:
                                        # Oder verwende direkt
                                        value = charger_val
                                except (ValueError, TypeError):
                                    pass
                            
                            # Fallback: Default
                            if value is None:
                                value = 1
                    
                    # UUID generieren wenn fehlend und Pflichtfeld
                    if pg_col == 'UUID' and (value is None or value == '') and pg_col in required_columns:
                        value = self._generate_uuid(row_dict, pg_table)
                    
                    # Datumswert konvertieren
                    if pg_col in date_columns and value is not None:
                        value = self._convert_datetime(value, pg_col)
                    
                    # Foreign Key Mapping (nur wenn noch nicht durch spezielle Logik gesetzt)
                    if pg_col in fk_columns and value is not None:
                        # Für CellLibrary: project_id wurde bereits gesetzt, nicht überschreiben
                        if sqlite_table == 'CellLibrary' and pg_col == 'project_id':
                            pass  # Wert behalten
                        else:
                            old_id = value
                            if old_id:
                                # ID mappen (wenn bereits migriert)
                                fk_table = pg_col.replace('_id', '')
                                # Tabelle finden (z.B. project_id -> megacellcnc_projects)
                                for table in self.MIGRATION_ORDER:
                                    if fk_table in table or table.endswith(f'_{fk_table}'):
                                        if table in self.id_mapping and old_id in self.id_mapping[table]:
                                            value = self.id_mapping[table][old_id]
                                            break
                                else:
                                    value = None  # Foreign Key noch nicht migriert
                    
                    # NULL-Werte korrekt behandeln
                    if value == '':
                        value = None
                    
                    # Pflichtfeld prüfen
                    if value is None and pg_col in required_columns:
                        # Default-Werte für Pflichtfelder
                        if pg_col == 'UUID':
                            value = self._generate_uuid(row_dict, pg_table) or f"MIGRATED-{uuid_lib.uuid4().hex[:12].upper()}"
                        elif pg_col in ['voltage', 'capacity', 'esr', 'esr_ac', 'min_voltage', 'max_voltage', 'store_voltage', 'store_Voltage']:
                            value = 0.0
                        elif pg_col in ['test_duration', 'charge_duration', 'discharge_duration', 'action_running_time']:
                            value = 0.0
                        elif pg_col in ['device_slot', 'cycles_count', 'testing_current', 'discharge_cycles_set', 'completed_cycles']:
                            value = 0
                        elif pg_col in ['temp_before_test', 'avg_temp_charging', 'avg_temp_discharging', 'max_temp_charging', 'max_temp_discharging']:
                            value = 0
                        elif pg_col in ['max_capacity', 'chg_current', 'pre_chg_current', 'ter_chg_current', 'discharge_current', 'discharge_resistance', 'discharge_mod', 'max_temp', 'low_volt_max_time', 'max_charge_duration', 'discharge_cycles']:
                            value = 0
                        elif pg_col in ['status', 'available', 'cell_type', 'device_type', 'discharge_mode', 'name']:
                            value = 'Unknown'
                        elif pg_col == 'device_ip' or pg_col == 'ip':
                            value = '0.0.0.0'
                        elif pg_col == 'device_mac' or pg_col == 'mac':
                            value = '00:00:00:00:00:00'
                        elif pg_col == 'type':
                            value = 'Unknown'
                        elif pg_col == 'bat_position':
                            value = ''
                        elif pg_col == 'runtime':
                            # DurationField braucht ein timedelta
                            from datetime import timedelta
                            value = timedelta(0)
                        elif pg_col == 'project_id':
                            # Foreign Key - überspringe Zeile wenn nicht vorhanden
                            logging.warning(f"Pflichtfeld project_id ist NULL in {pg_table}, überspringe Zeile")
                            skip_row = True
                            break
                        elif pg_col == 'device_id':
                            # Foreign Key - überspringe Zeile wenn nicht vorhanden
                            logging.warning(f"Pflichtfeld device_id ist NULL in {pg_table}, überspringe Zeile")
                            skip_row = True
                            break
                        else:
                            # Versuche generische Defaults basierend auf Typ
                            with django_connection.cursor() as type_cursor:
                                type_cursor.execute("""
                                    SELECT data_type
                                    FROM information_schema.columns
                                    WHERE table_name = %s AND column_name = %s
                                """, [pg_table, pg_col])
                                col_type_result = type_cursor.fetchone()
                                if col_type_result:
                                    col_type = col_type_result[0]
                                    if 'int' in col_type.lower():
                                        value = 0
                                    elif 'float' in col_type.lower() or 'double' in col_type.lower() or 'numeric' in col_type.lower():
                                        value = 0.0
                                    elif 'char' in col_type.lower() or 'text' in col_type.lower():
                                        value = ''
                                    elif 'bool' in col_type.lower():
                                        value = False
                                    else:
                                        logging.warning(f"Pflichtfeld {pg_col} ({col_type}) ist NULL in {pg_table}, überspringe Zeile")
                                        skip_row = True
                                        break
                                else:
                                    logging.warning(f"Pflichtfeld {pg_col} ist NULL in {pg_table}, überspringe Zeile")
                                    skip_row = True
                                    break
                    
                    # Immer hinzufügen (auch NULL-Werte können wichtig sein)
                    values.append(value)
                    pg_cols_clean.append(pg_col)
                
                # Zeile überspringen wenn nötig
                if skip_row:
                    skipped_count += 1
                    # DEBUG für erste übersprungene Zeile
                    if skipped_count == 1:
                        print(f"\n  DEBUG: Erste Zeile übersprungen!")
                        print(f"  DEBUG: pg_columns={len(pg_columns)}, values={len(values)}")
                        print(f"  DEBUG: Letzte 5 pg_cols: {pg_cols_clean[-5:] if len(pg_cols_clean) > 5 else pg_cols_clean}")
                        print(f"  DEBUG: Letzte 5 values: {values[-5:] if len(values) > 5 else values}")
                    continue
                
                # INSERT
                if values:
                    placeholders = ','.join(['%s'] * len(values))
                    # Spalten in Anführungszeichen setzen für case-sensitive Namen
                    cols_str = ','.join([f'"{col}"' for col in pg_cols_clean])
                    
                    try:
                        sql = f"""
                            INSERT INTO {pg_table} ({cols_str}) 
                            VALUES ({placeholders})
                            ON CONFLICT DO NOTHING
                            RETURNING id
                        """
                        cursor.execute(sql, values)
                        result = cursor.fetchone()
                        if result:
                            # ID Mapping speichern
                            old_id = row_dict.get('id') if id_col_sqlite else None
                            if old_id:
                                self.id_mapping[pg_table][old_id] = result[0]
                            migrated_count += 1
                    except Exception as e:
                        error_msg = f"Fehler bei Zeile in {pg_table}: {e}"
                        print(f"  ⚠ {error_msg}")
                        logging.error(f"{error_msg} | Row data: {row_dict}")
                        continue
            
            django_connection.commit()
            print(f"  ✓ {migrated_count} von {len(rows)} Zeilen migriert")
            if skipped_count > 0:
                print(f"  ⚠ {skipped_count} Zeilen übersprungen (fehlende Pflichtfelder)")


def main():
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"❌ Fehler: SQLite-DB nicht gefunden: {SQLITE_DB_PATH}")
        print(f"   Bitte Pfad in SQLITE_DB_PATH anpassen!")
        return
    
    # 1. SQLite analysieren
    analyzer = SQLiteAnalyzer(SQLITE_DB_PATH)
    sqlite_tables = analyzer.analyze()
    
    # 2. Mapping erstellen
    mapper = AutoMapper(sqlite_tables)
    table_mapping, column_mapping = mapper.create_mapping()
    
    # 3. Mapping anzeigen
    print("\n=== Mapping-Übersicht ===")
    for pg_table, sqlite_table in table_mapping.items():
        print(f"\n{sqlite_table} -> {pg_table}")
        for pg_col, sqlite_col in column_mapping[pg_table].items():
            if sqlite_col:
                print(f"  {pg_col} <- {sqlite_col}")
    
    # 4. Bestätigung
    print("\n" + "="*50)
    response = input("\nMigration starten? (j/n): ")
    if response.lower() != 'j':
        print("Abgebrochen.")
        analyzer.close()
        return
    
    # 5. Migration durchführen
    migrator = DataMigrator(analyzer, mapper)
    migrator.migrate()
    
    analyzer.close()
    print("\n=== Migration abgeschlossen ===")
    print(f"\nFehler-Log gespeichert in: {LOG_FILE}")
    print(f"Für weitere Logs siehe:")
    print(f"  - Docker Container Logs: docker-compose logs web")
    print(f"  - PostgreSQL Logs: docker-compose logs db")


if __name__ == "__main__":
    main()

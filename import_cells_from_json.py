#!/usr/bin/env python3
"""
Import Cells from JSON Export
Importiert Zellen aus CellLibrary JSON-Export in PostgreSQL
"""

import os
import sys
import json
import django
from datetime import datetime, timedelta
import pytz

# Django Setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
django.setup()

from megacellcnc.models import Projects, Cells
from django.db import connection as django_connection


class CellImporter:
    def __init__(self, json_file):
        self.json_file = json_file
        self.stats = {
            'total': 0,
            'imported': 0,
            'skipped': 0,
            'errors': 0
        }
        self.projects = {}  # Cache für Projects: {name: project_obj}
        
    def _get_or_create_project(self, project_name):
        """Holt oder erstellt ein Project"""
        if not project_name or project_name.strip() == '':
            project_name = 'Importierte Zellen'
        
        # Aus Cache holen wenn vorhanden
        if project_name in self.projects:
            return self.projects[project_name]
        
        # Project erstellen oder holen
        project, created = Projects.objects.get_or_create(
            Name=project_name,
            defaults={
                'CellType': '18650',
                'Notes': 'Automatisch importiert aus JSON',
                'LastCellNumber': 0,
                'Status': 'Active',
                'TotalCells': 0,
                'DevCnt': 0
            }
        )
        
        # In Cache speichern
        self.projects[project_name] = project
        
        if created:
            print(f"  ✓ Project '{project_name}' erstellt (ID: {project.id})")
        
        return project
    
    def _generate_uuid(self, cell_data):
        """Generiert UUID im Format D{YYYYMMDD}-S{SerialNumber:06d}"""
        cell_serial = cell_data.get('CellSerialNumber')
        log_date = cell_data.get('LogDate')
        
        if cell_serial and log_date:
            try:
                # Parse LogDate
                if isinstance(log_date, str):
                    date_obj = datetime.strptime(log_date.split('.')[0], '%Y-%m-%d %H:%M:%S')
                else:
                    date_obj = log_date
                
                date_str = date_obj.strftime('%Y%m%d')
                return f"D{date_str}-S{int(cell_serial):06d}"
            except Exception as e:
                print(f"  ⚠ Fehler beim UUID-Generieren: {e}")
        
        # Fallback
        if cell_serial:
            date_str = datetime.now().strftime('%Y%m%d')
            return f"D{date_str}-S{int(cell_serial):06d}"
        
        return None
    
    def _convert_available(self, value):
        """Konvertiert Available-Wert zu Yes/No String"""
        if value == 1 or value == '1':
            return 'Yes'
        elif value == 0 or value == '0':
            return 'No'
        elif value == "b''" or value == '':
            return 'Yes'  # Empty = Available
        else:
            return 'Yes'  # Default
    
    def _parse_datetime(self, value):
        """Parsed Datetime-String und macht es timezone-aware"""
        if not value or value == '':
            return None
        
        try:
            if isinstance(value, str):
                # Format: "2022-09-09 16:49:13.5815584"
                dt = datetime.strptime(value.split('.')[0], '%Y-%m-%d %H:%M:%S')
                # Make timezone-aware (UTC)
                return pytz.UTC.localize(dt)
            return value
        except Exception:
            return None
    
    def _safe_float(self, value, default=0.0):
        """Konvertiert sicher zu Float"""
        try:
            return float(value) if value not in [None, '', 'b\'\''] else default
        except (ValueError, TypeError):
            return default
    
    def _safe_int(self, value, default=0):
        """Konvertiert sicher zu Int"""
        try:
            return int(value) if value not in [None, '', 'b\'\''] else default
        except (ValueError, TypeError):
            return default
    
    def _import_cell(self, cell_data):
        """Importiert eine einzelne Zelle"""
        try:
            # Project holen/erstellen
            project_name = cell_data.get('ProjectName', 'Importierte Zellen')
            project = self._get_or_create_project(project_name)
            
            # UUID generieren
            uuid = self._generate_uuid(cell_data)
            if not uuid:
                print(f"  ⚠ Überspringe Zelle: Keine UUID generierbar")
                self.stats['skipped'] += 1
                return False
            
            # Prüfen ob Zelle bereits existiert
            if Cells.objects.filter(UUID=uuid).exists():
                self.stats['skipped'] += 1
                return False
            
            # Available Status konvertieren
            available = self._convert_available(cell_data.get('Available', 1))
            
            # Parse LogDate für insertion und removal_date
            log_date = self._parse_datetime(cell_data.get('LogDate'))
            
            # Cell erstellen
            cell = Cells(
                UUID=uuid,
                project=project,
                available=available,
                capacity=self._safe_float(cell_data.get('capacity', 0)),
                voltage=self._safe_float(cell_data.get('voltage', 0)),
                esr=self._safe_float(cell_data.get('esr', 0)),
                esr_ac=self._safe_float(cell_data.get('esr_ac', 0)),
                min_voltage=self._safe_float(cell_data.get('min_voltage', 2.8)),
                max_voltage=self._safe_float(cell_data.get('max_voltage', 4.25)),
                store_voltage=self._safe_float(cell_data.get('store_voltage', 3.4)),
                temp_before_test=self._safe_float(cell_data.get('temperature', 0)),
                cycles_count=self._safe_int(cell_data.get('discharge_cycles', 0)),
                test_duration=self._safe_float(cell_data.get('action_length', 0)),
                insertion_date=log_date,
                removal_date=log_date,  # TestDate = LogDate
                cell_type='18650',  # Aktuell nur dieser Type
                device_ip=cell_data.get('charger_icc', '192.168.1.33'),
                device_slot=self._safe_int(cell_data.get('CCiD', 0)),
                device_mac='00:00:00:00:00:00',
                device_type=cell_data.get('charger_type', 'McC'),
                charge_duration=0.0,
                discharge_duration=0.0,
                avg_temp_charging=0,
                avg_temp_discharging=0,
                max_temp_charging=0,
                max_temp_discharging=0,
                testing_current=0,
                discharge_mode='CC',
                status='Completed',
                bat_position='',
                battery=None
            )
            
            cell.save()
            self.stats['imported'] += 1
            return True
            
        except Exception as e:
            print(f"  ⚠ Fehler beim Importieren: {e}")
            self.stats['errors'] += 1
            return False
    
    def truncate_tables(self):
        """Leert Ziel-Tabellen"""
        print("\n=== Leere Ziel-Tabellen ===\n")
        with django_connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE megacellcnc_cells CASCADE;")
            print("  ✓ megacellcnc_cells geleert")
            
            cursor.execute("TRUNCATE TABLE megacellcnc_projects CASCADE;")
            print("  ✓ megacellcnc_projects geleert")
            
            django_connection.commit()
    
    def import_cells(self):
        """Hauptfunktion für Import"""
        print(f"\n=== Importiere Zellen aus JSON ===\n")
        print(f"Datei: {self.json_file}\n")
        
        # JSON laden
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                cells_data = json.load(f)
        except Exception as e:
            print(f"❌ Fehler beim Laden der JSON-Datei: {e}")
            return False
        
        self.stats['total'] = len(cells_data)
        print(f"Gefunden: {self.stats['total']} Zellen\n")
        
        # Zellen importieren
        for i, cell_data in enumerate(cells_data, 1):
            self._import_cell(cell_data)
            
            # Progress anzeigen
            if i % 1000 == 0:
                print(f"  Fortschritt: {i}/{self.stats['total']} "
                      f"(Importiert: {self.stats['imported']}, "
                      f"Übersprungen: {self.stats['skipped']}, "
                      f"Fehler: {self.stats['errors']})")
        
        # Finale Statistik
        print(f"\n=== Import abgeschlossen ===\n")
        print(f"  Gesamt:        {self.stats['total']}")
        print(f"  ✓ Importiert:  {self.stats['imported']}")
        print(f"  ⊘ Übersprungen: {self.stats['skipped']}")
        print(f"  ✗ Fehler:      {self.stats['errors']}\n")
        
        return True


def main():
    print("="*60)
    print("Cell Import von JSON")
    print("="*60)
    
    # JSON-Datei (im Container ist /home/heinz/megacnc als /app gemountet)
    json_file = '/app/CellLibrary_export_2026-01-20_194052.json'
    
    if not os.path.exists(json_file):
        print(f"❌ JSON-Datei nicht gefunden: {json_file}")
        return
    
    # Bestätigung
    print(f"\nJSON-Datei: {json_file}")
    print("\n⚠️  WARNUNG: Tabellen megacellcnc_cells und megacellcnc_projects werden geleert!")
    response = input("\nImport starten? (j/n): ")
    
    if response.lower() != 'j':
        print("Import abgebrochen.")
        return
    
    # Import ausführen
    importer = CellImporter(json_file)
    importer.truncate_tables()
    importer.import_cells()


if __name__ == '__main__':
    main()

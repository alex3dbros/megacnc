#!/usr/bin/env python3
"""
Update Test Dates from UUID
Extrahiert das Testdatum aus der UUID und füllt removal_date
"""

import os
import sys
import django
from datetime import datetime
import pytz

# Django Setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
django.setup()

from megacellcnc.models import Cells
from django.db import transaction


def extract_date_from_uuid(uuid):
    """
    Extrahiert Datum aus UUID
    Format: D20231020-S016670 -> 2023-10-20
    """
    if not uuid or len(uuid) < 9:
        return None
    
    try:
        # UUID Format: D{YYYYMMDD}-S{SerialNo}
        date_part = uuid[1:9]  # YYYYMMDD
        year = date_part[0:4]
        month = date_part[4:6]
        day = date_part[6:8]
        
        # Create timezone-aware datetime (midnight UTC)
        dt = datetime(int(year), int(month), int(day), 0, 0, 0)
        return pytz.UTC.localize(dt)
    except Exception as e:
        print(f"  ⚠ Fehler beim Parsen von UUID '{uuid}': {e}")
        return None


def update_test_dates():
    """Hauptfunktion: Update aller Cells"""
    print("="*60)
    print("Update Test Dates from UUID")
    print("="*60)
    
    # Statistiken
    stats = {
        'total': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    
    # Alle Cells ohne removal_date
    cells_without_date = Cells.objects.filter(removal_date__isnull=True)
    stats['total'] = cells_without_date.count()
    
    print(f"\nGefunden: {stats['total']} Cells ohne TestDate")
    
    if stats['total'] == 0:
        print("\n✓ Alle Cells haben bereits ein TestDate!")
        return
    
    # Bestätigung
    response = input(f"\nTestDate für {stats['total']} Cells aus UUID extrahieren? (j/n): ")
    if response.lower() != 'j':
        print("Update abgebrochen.")
        return
    
    print("\n=== Starte Update ===\n")
    
    # Batch Update für Performance
    with transaction.atomic():
        for i, cell in enumerate(cells_without_date, 1):
            try:
                # Extrahiere Datum aus UUID
                test_date = extract_date_from_uuid(cell.UUID)
                
                if test_date:
                    cell.removal_date = test_date
                    cell.save(update_fields=['removal_date'])
                    stats['updated'] += 1
                else:
                    stats['skipped'] += 1
                
                # Progress anzeigen
                if i % 1000 == 0:
                    print(f"  Fortschritt: {i}/{stats['total']} "
                          f"(Updated: {stats['updated']}, "
                          f"Übersprungen: {stats['skipped']}, "
                          f"Fehler: {stats['errors']})")
                    
            except Exception as e:
                print(f"  ⚠ Fehler bei Cell {cell.id}: {e}")
                stats['errors'] += 1
    
    # Finale Statistik
    print(f"\n=== Update abgeschlossen ===\n")
    print(f"  Gesamt:        {stats['total']}")
    print(f"  ✓ Aktualisiert: {stats['updated']}")
    print(f"  ⊘ Übersprungen: {stats['skipped']}")
    print(f"  ✗ Fehler:      {stats['errors']}\n")


if __name__ == '__main__':
    update_test_dates()

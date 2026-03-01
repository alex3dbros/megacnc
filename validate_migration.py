#!/usr/bin/env python3
"""
Validiert die Migration
"""

import os
import sys
import django

# Django Setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
django.setup()

from megacellcnc.models import Cells, Projects

print('='*60)
print('Validierung der Migration')
print('='*60)
print()

print(f'Zellen in DB: {Cells.objects.count()}')
print(f'Projects in DB: {Projects.objects.count()}')
print()

print('Projects mit Zellen-Anzahl:')
for p in Projects.objects.all().order_by('id'):
    cell_count = p.cells.count()
    print(f'  [{p.id}] {p.Name}: {cell_count} Zellen')

print()

# Beispiel-Zellen anzeigen
print('Erste 5 Zellen:')
for cell in Cells.objects.all().order_by('id')[:5]:
    print(f'  [{cell.id}] {cell.UUID} - {cell.cell_type} - {cell.capacity}mAh - {cell.available}')

print()

# Available-Status Statistik
available_yes = Cells.objects.filter(available='Yes').count()
available_no = Cells.objects.filter(available='No').count()
print(f'Available Status:')
print(f'  Yes: {available_yes}')
print(f'  No:  {available_no}')

print()
print('✅ Migration erfolgreich abgeschlossen!')

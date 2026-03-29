#!/bin/bash
# QZ Tray starten (falls nicht bereits aktiv)

if pgrep -f "qz-tray" > /dev/null; then
    echo "QZ Tray läuft bereits (PID: $(pgrep -f qz-tray | head -1))"
else
    /opt/qz-tray/qz-tray &
    sleep 2
    echo "QZ Tray gestartet"
fi

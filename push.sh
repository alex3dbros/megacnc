#!/bin/bash

# Commit-Message als Parameter oder Standard
MSG="${1:-Update}"

# Alles committen im developer Branch
git add -A
git commit -m "$MSG"

# Zu main wechseln und developer mergen
git checkout main
git merge developer
git push origin main

# Zurück zum developer Branch
git checkout developer

echo "Fertig: Änderungen committed, in main gemergt, gepusht und zurück auf developer."

#!/usr/bin/env bash
# Kompatibilitaet: leitet auf das Root-Skript um (./update.sh ist kanonisch).
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$REPO_ROOT/update.sh" "$@"

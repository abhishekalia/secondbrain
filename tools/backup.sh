#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/ak"
ts=$(date +"%Y%m%d-%H%M%S")
mkdir -p backups
tar --exclude='.venv' --exclude='backups' -czf "backups/ak-$ts.tgz" .
echo "Backup: backups/ak-$ts.tgz"

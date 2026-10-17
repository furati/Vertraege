#!/usr/bin/env bash
# telekom-archiv.sh – Telekom-/Streaming-Mails archivieren, Index bauen, committen.
#
#   ./scripts/telekom-archiv.sh            # archivieren + Index + Commit (fragt vor dem Push)
#   ./scripts/telekom-archiv.sh --dry-run  # nur anzeigen, was neu wäre
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

SEIT="${SEIT:-2026/10/12}"
ZIEL="telekom/mails"
QUERY="after:${SEIT} (from:telekom.de OR from:account.netflix.com OR from:disneyplus.com OR from:my.disney.com OR from:rtlplus.com OR from:paramountplus.com OR (from:apple.com \"Apple TV\")) -category:promotions"

./scripts/mail-archiv.py --query "$QUERY" --ziel "$ZIEL" "$@"

if [[ " $* " == *" --dry-run "* ]]; then
  exit 0
fi

./scripts/mail-index.py "$ZIEL"

if [[ -n "$(git status --porcelain -- "$ZIEL")" ]]; then
  git add "$ZIEL"
  git commit -m "Mail-Archiv Telekom aktualisiert ($(date +%F))"
  read -r -p "Nach GitHub pushen? [j/N] " antwort
  [[ "$antwort" =~ ^[jJyY]$ ]] && git push
else
  echo "Keine neuen Mails."
fi

#!/usr/bin/env python3
"""
mail-index.py – erzeugt <ordner>/README.md als chronologische Übersicht
aller archivierten Mails (liest die Kopfdaten aus */mail.md).

  ./scripts/mail-index.py telekom/mails
"""
import re
import sys
from pathlib import Path


def feld(text: str, name: str) -> str:
    m = re.search(rf"^{name}:\s*(.*)$", text, re.M)
    return m.group(1).strip() if m else ""


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    ordner = Path(sys.argv[1])
    zeilen = []
    for md in sorted(ordner.glob("*/mail.md")):
        t = md.read_text(encoding="utf-8")
        von = feld(t, "von")
        von = re.sub(r"\s*<.*?>", "", von).strip('" ') or von
        anh = feld(t, "anhaenge").strip("[]")
        zeilen.append(
            f"| {feld(t, 'datum')[:16]} | {von} | [{feld(t, 'betreff')}]({md.parent.name}/mail.md) | {anh} |"
        )
    inhalt = [
        "# Mail-Archiv",
        "",
        "Automatisch erzeugt mit `scripts/mail-index.py` – nicht von Hand bearbeiten.",
        "Mails mit Zugangsdaten, PINs und Einmal-Codes werden bewusst nicht archiviert.",
        "",
        "| Datum | Von | Betreff | Anhänge |",
        "|---|---|---|---|",
        *zeilen,
        "",
    ]
    (ordner / "README.md").write_text("\n".join(inhalt), encoding="utf-8")
    print(f"{len(zeilen)} Mails im Index: {ordner / 'README.md'}")


if __name__ == "__main__":
    main()

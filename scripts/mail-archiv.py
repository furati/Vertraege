#!/usr/bin/env python3
"""
mail-archiv.py – Mails aus Gmail per IMAP ins Repo archivieren (inkl. PDF-Anhänge).

Pro Mail entsteht ein Ordner  <ziel>/<JJJJ-MM-TT_HHMM>_<betreff>/  mit:
  mail.md        Kopfdaten + Klartext (Tracking-Links entfernt)
  *.pdf …        Anhänge (Logos/Inline-Bilder werden übersprungen)
  mail.eml       Original-Mail (nur mit --eml)

Bereits archivierte Mails (gleiche Message-ID) werden übersprungen, das Skript
kann also beliebig oft laufen. Mails mit Zugangsdaten/PINs/Codes werden per
Betreff-Muster ausgelassen – die gehören in den Passwortmanager, nicht ins Repo.

Voraussetzungen
  - Gmail: IMAP aktiviert, 2FA an, App-Passwort angelegt
    (https://myaccount.google.com/apppasswords)
  - App-Passwort über eine dieser Quellen:
      GMAIL_APP_PASSWORD=...                      (Umgebungsvariable)
      macOS-Schlüsselbund:  security add-generic-password -s gmail-imap -a <user> -w
      pass:                 pass insert gmail/imap

Beispiele
  ./scripts/mail-archiv.py --query 'from:telekom.de after:2026/10/12' --ziel telekom/mails
  ./scripts/mail-archiv.py --query 'label:Telekom' --ziel telekom/mails --dry-run
"""
import argparse
import email
import email.policy
import imaplib
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

IMAP_HOST = "imap.gmail.com"
DEFAULT_USER = "ralf@buhlrich.com"

# Mails mit Geheimnissen – werden nie archiviert
GEHEIM_MUSTER = [
    r"zugangsdaten",
    r"benutzer-pin",
    r"\bpin\b",
    r"zugangs-code",
    r"bestätigungscode",
    r"passcode",
    r"login-code",
    r"einmal(iger)?\s*code",
    r"kennwort",
    r"passwort",
]

# Anhänge, die nur Deko sind
DEKO_ANHANG = re.compile(r"(logo|laptop|^\d+\.png$|^image\d*\.)", re.I)


def app_passwort(user: str) -> str:
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    if pw:
        return pw.strip()
    if shutil.which("security"):
        r = subprocess.run(
            ["security", "find-generic-password", "-s", "gmail-imap", "-a", user, "-w"],
            capture_output=True, text=True,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    if shutil.which("pass"):
        r = subprocess.run(["pass", "show", "gmail/imap"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.splitlines()[0].strip()
    sys.exit("Kein App-Passwort gefunden (GMAIL_APP_PASSWORD, Schlüsselbund 'gmail-imap' oder pass gmail/imap).")


def slug(text: str, maxlen: int = 60) -> str:
    text = text.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:maxlen].rstrip("-") or "ohne-betreff"


def ist_geheim(betreff: str) -> bool:
    b = betreff.lower()
    return any(re.search(m, b) for m in GEHEIM_MUSTER)


def html_zu_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", "", html)
    html = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</h\d>", "\n", html)
    text = re.sub(r"<[^>]+>", "", html)
    import html as h
    return h.unescape(text)


def text_aufraeumen(text: str) -> str:
    # Tracking-/Token-Links entfernen, Domain behalten
    text = re.sub(r"\(?\s*https?://[^\s\)\]]+\s*\)?", " ", text)
    text = re.sub(r"\[\s*\]", "", text)
    text = re.sub(r"[ \t͏‌ ]+", " ", text)
    text = re.sub(r"^\s*\|?\s*\|?\s*$", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def koerper(msg) -> str:
    teil = msg.get_body(preferencelist=("plain", "html"))
    if teil is None:
        return ""
    inhalt = teil.get_content()
    if teil.get_content_type() == "text/html":
        inhalt = html_zu_text(inhalt)
    return text_aufraeumen(inhalt)


def bekannte_ids(ziel: Path) -> set:
    ids = set()
    for md in ziel.glob("*/mail.md"):
        m = re.search(r"^message-id:\s*(.+)$", md.read_text(encoding="utf-8"), re.M)
        if m:
            ids.add(m.group(1).strip())
    return ids


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--query", required=True, help="Gmail-Suchsyntax, z. B. 'from:telekom.de after:2026/10/12'")
    ap.add_argument("--ziel", required=True, help="Zielordner im Repo, z. B. telekom/mails")
    ap.add_argument("--user", default=os.environ.get("GMAIL_USER", DEFAULT_USER))
    ap.add_argument("--eml", action="store_true", help="Original-Mail zusätzlich als .eml ablegen")
    ap.add_argument("--dry-run", action="store_true", help="nur anzeigen, nichts schreiben")
    args = ap.parse_args()

    ziel = Path(args.ziel)
    ziel.mkdir(parents=True, exist_ok=True)
    schon_da = bekannte_ids(ziel)

    imap = imaplib.IMAP4_SSL(IMAP_HOST)
    imap.login(args.user, app_passwort(args.user))
    imap.select('"[Gmail]/All Mail"', readonly=True)
    status, daten = imap.search(None, "X-GM-RAW", f'"{args.query}"')
    if status != "OK":
        sys.exit(f"Suche fehlgeschlagen: {daten}")
    nummern = daten[0].split()
    print(f"{len(nummern)} Treffer für: {args.query}")

    neu = uebersprungen = geheim = 0
    for nr in nummern:
        status, roh = imap.fetch(nr, "(RFC822)")
        if status != "OK":
            continue
        raw = roh[0][1]
        msg = email.message_from_bytes(raw, policy=email.policy.default)
        betreff = str(msg.get("Subject", "")).strip()
        mid = str(msg.get("Message-ID", "")).strip()
        datum = parsedate_to_datetime(msg["Date"]).astimezone() if msg["Date"] else datetime.now()

        if ist_geheim(betreff):
            geheim += 1
            print(f"  [geheim, ausgelassen] {datum:%d.%m. %H:%M} {betreff}")
            continue
        if mid in schon_da:
            uebersprungen += 1
            continue

        ordner = ziel / f"{datum:%Y-%m-%d_%H%M}_{slug(betreff)}"
        # Ordner existiert schon (z. B. von Hand angelegt, ohne Anhänge)?
        # Dann nur fehlende Anhänge nachladen.
        nachtrag = ordner.exists() and (ordner / "mail.md").exists()
        anhaenge = []
        for teil in msg.iter_attachments():
            name = teil.get_filename() or ""
            if not name or DEKO_ANHANG.search(name):
                continue
            anhaenge.append((name, teil.get_payload(decode=True)))

        if nachtrag:
            fehlend = [(n, i) for n, i in anhaenge if not (ordner / n.replace("/", "_")).exists()]
            if not fehlend:
                uebersprungen += 1
                continue
            print(f"  [Anhänge nachladen] {datum:%d.%m. %H:%M} {betreff}  (+{len(fehlend)})")
            if not args.dry_run:
                for name, inhalt in fehlend:
                    (ordner / name.replace("/", "_")).write_bytes(inhalt)
                md = ordner / "mail.md"
                t = md.read_text(encoding="utf-8")
                t = re.sub(r"^anhaenge:.*$", f"anhaenge: [{', '.join(n for n, _ in anhaenge)}]", t, count=1, flags=re.M)
                if not re.search(r"^message-id:", t, re.M):
                    t = t.replace("\n---\n", f"\nmessage-id: {mid}\n---\n", 1)
                md.write_text(t, encoding="utf-8")
            neu += 1
            continue

        print(f"  [neu] {datum:%d.%m. %H:%M} {betreff}" + (f"  (+{len(anhaenge)} Anhang/Anhänge)" if anhaenge else ""))
        if args.dry_run:
            neu += 1
            continue

        ordner.mkdir(parents=True, exist_ok=True)
        kopf = [
            "---",
            f"betreff: {betreff}",
            f"von: {msg.get('From', '')}",
            f"an: {msg.get('To', '')}",
            f"datum: {datum:%Y-%m-%d %H:%M %z}",
            f"message-id: {mid}",
            f"anhaenge: [{', '.join(n for n, _ in anhaenge)}]",
            "---",
            "",
            f"# {betreff}",
            "",
            "",
        ]
        (ordner / "mail.md").write_text("\n".join(kopf) + koerper(msg) + "\n", encoding="utf-8")
        for name, inhalt in anhaenge:
            (ordner / name.replace("/", "_")).write_bytes(inhalt)
        if args.eml:
            (ordner / "mail.eml").write_bytes(raw)
        neu += 1

    imap.logout()
    print(f"Fertig: {neu} neu, {uebersprungen} schon archiviert, {geheim} wegen Geheimnissen ausgelassen.")
    if not args.dry_run and neu:
        print("Index aktualisieren:  ./scripts/mail-index.py " + str(ziel))


if __name__ == "__main__":
    main()

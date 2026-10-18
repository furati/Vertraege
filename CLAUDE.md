# Kontext für Claude (und für Ralf)

Dieses Repo ist Ralfs private Ablage für Verträge und Abos. Diese Datei ist das
„Gedächtnis“: Sie hält fest, was bisher passiert ist, wie das Repo aufgebaut ist und
welche Regeln gelten – damit eine neue Sitzung ohne Vorgeschichte weiterarbeiten kann.

## Regeln

- **Keine Geheimnisse ins Repo**: keine Passwörter, PINs, Einmal-Codes, Zugangsdaten-PDFs,
  keine Konto-Tokens aus Links. Die gehören in den Passwortmanager.
  `scripts/mail-archiv.py` lässt solche Mails per Betreff-Muster automatisch aus.
- Repo ist **privat**. Kundennummern, Auftragsnummern und Rufnummern dürfen hier stehen.
- Sprache: Deutsch.
- Commits auf `main`, Push nach `origin` (github.com/furati/Vertraege).

## Aufbau

```
README.md                  Übersicht aller Verträge
CLAUDE.md                  diese Datei (Kontext/Gedächtnis)
<anbieter>/<vertrag>.md    Zusammenfassung: Vertragsdaten, Status, offene Punkte, Mail-Chronologie
<anbieter>/mails/          Mail-Archiv, ein Ordner pro Mail (mail.md + Anhänge), README.md = Index
<anbieter>/dokumente/      lose Dokumente (z. B. PDFs, die nicht per Mail kamen)
scripts/                   Hilfsskripte, von Hand ausführbar
```

## Skripte

| Skript | Zweck |
|---|---|
| `scripts/mail-archiv.py` | Holt Mails per Gmail-IMAP (Suchsyntax wie in Gmail) und legt sie samt PDF-Anhängen ab. Idempotent: schon archivierte Mails werden übersprungen, bei von Hand angelegten Ordnern werden nur fehlende Anhänge nachgeladen. |
| `scripts/mail-index.py <ordner>` | Baut `<ordner>/README.md` als chronologischen Index. |
| `scripts/telekom-archiv.sh` | Fertige Abfrage für Telekom + Streamingdienste → Archiv → Index → Commit → Push (mit Rückfrage). `--dry-run` zeigt nur an. |

Einmalige Einrichtung für die Skripte:
1. Gmail: IMAP aktivieren, App-Passwort anlegen (https://myaccount.google.com/apppasswords).
2. App-Passwort ablegen, z. B. macOS: `security add-generic-password -s gmail-imap -a ralf@buhlrich.com -w`
   (alternativ `GMAIL_APP_PASSWORD` setzen oder `pass insert gmail/imap`).
3. `./scripts/telekom-archiv.sh --dry-run`, danach ohne `--dry-run`.

## Verlauf

### Telekom MagentaZuhause XL mit MagentaTV MegaStream (Oktober 2026)

- 13.10.2026: Ralf bucht MagentaZuhause XL mit MagentaTV MegaStream (Auftrag 80353203229),
  am selben Tag auch ein Mobilfunk-Auftrag.
- 17.10.2026: Zweiter Festnetz-Auftrag 91183779190 (vermutlich Netflix-Upgrade auf Premium),
  sofort ausgeführt. Danach Aktivierung der Streamingdienste:
  - Netflix Premium: bestehendes Konto übernommen, Zahlung läuft über Telekom ✅
  - Disney+ Standard: Konto angelegt ✅ (Willkommensmail 18.10., Nutzungsvertrag archiviert)
  - RTL+ Premium: registriert, E-Mail bestätigt ✅
  - Apple TV: über Telekom-Link registriert, Apple bestätigt nur am Bildschirm (keine Mail) ✅
  - Paramount+: nicht Teil von MegaStream, keine Buchung/Mail gefunden ❓
- Repo `furati/Vertraege` am 17.10.2026 angelegt. Mail-Texte vom 13.–17.10. übernommen
  (ohne Geheimnis-Mails). PDF-Anhänge fehlen noch → `scripts/telekom-archiv.sh` ausführen.

Details und offene Punkte: `telekom/megastream.md`.

## Offen (Stand 17.10.2026)

- [ ] PDF-Anhänge per `scripts/telekom-archiv.sh` nachladen (Vertragszusammenfassung, Auftragsbestätigungen, Preislisten)
- [ ] Preise, Mindestlaufzeit, Kündigungsfrist aus der Vertragszusammenfassung in `telekom/megastream.md` eintragen
- [ ] Paramount+ klären
- [ ] Alte Direkt-Abos (Disney+, Apple TV, RTL+) prüfen und ggf. kündigen
- [ ] Noch nicht archiviert (vom Skript erfasst): zweite Netflix-Gerätemail (08:25)

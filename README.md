# Verträge

Übersicht über laufende Verträge und Abos.

| Vertrag | Übersicht | Mail-Archiv |
|---|---|---|
| Telekom MagentaZuhause XL mit MagentaTV MegaStream | [telekom/megastream.md](telekom/megastream.md) | [telekom/mails/](telekom/mails/README.md) |

Kontext, Regeln und Verlauf: [CLAUDE.md](CLAUDE.md)

## Mail-Archiv aktualisieren

```sh
./scripts/telekom-archiv.sh --dry-run   # zeigt, was neu wäre
./scripts/telekom-archiv.sh             # archiviert, baut Index, committet, fragt vor dem Push
```

Einrichtung (Gmail-App-Passwort) siehe [CLAUDE.md](CLAUDE.md#skripte).

> Keine Passwörter, PINs oder Zugangscodes in diesem Repo ablegen – die gehören in den Passwortmanager.

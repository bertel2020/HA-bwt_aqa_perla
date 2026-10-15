# Änderungsprotokoll

*[🇬🇧 English version](CHANGELOG.en.md)*

Alle nennenswerten Änderungen an diesem Projekt werden hier dokumentiert.
Versionen folgen dem Feld `version` in
`custom_components/bwt_aqa_perla/manifest.json`.

## 1.0.0 – 2026-10-15

### Achtung beim Update

- **Gerätetyp** und **Regenerationsschritt** sind jetzt Enum-Sensoren. Der Zustand ist ein Schlüssel (`type_12`, `step_0`), die Anzeige wird übersetzt. Automationen oder Templates, die auf die bisherigen deutschen Texte prüfen, müssen angepasst werden. Unbekannte Werte liefern keinen Zustand mehr.
- Die **Sensorklassen** haben sich geändert: Wasserverbrauch 24 h sowie Soll- und Restkapazität sind reine Messwerte ohne Wasser-Geräteklasse. Der Spitzendurchfluss nutzt die Geräteklasse Durchflussrate.
- TCP-Einträge werden automatisch migriert (Unique-ID ohne `.0` am Port).
- Liter-Werte werden für **neue** Entities ohne Nachkommastellen angezeigt, der Salzverbrauch mit zwei. Bestehende Entities behalten ihre Anzeige, bis die Anzeigegenauigkeit in den Entity-Einstellungen geändert wird.

### Neu

- Sensoren „Restkapazität Säule 1/2 (Prozent)“ und Binärsensor „Regeneration aktiv“.
- Der Regenerationsschritt wird schneller abgefragt (Standard 15 s) als die übrigen Werte (Standard 60 s); beide Intervalle sind einstellbar.
- Auswahl erkannter serieller Ports im Assistenten; Dokumentation und Texte für ser2net.
- Verbindung (Port, Host, TCP-Port) lässt sich neu konfigurieren.
- Diagnose-Download mit geschwärzter Konfiguration, Werten und Roh-Frames.
- Sensoren werden nur für Werte angelegt, die die Anlage tatsächlich meldet.
- Das Gerät heißt wie der Konfigurationseintrag.
- Symbole für die Sensoren.

### Behoben

- Antworten auf einen anderen Befehl (Echo, verspätete oder fremde Antworten bei einem zweiten Client) brechen den Poll nicht mehr ab.
- Einzelne fehlgeschlagene Befehle machen nicht mehr alle Sensoren „nicht verfügbar“; Werte verfallen erst nach drei verpassten Abfragen.
- Skalierte Werte (Salzverbrauch) ohne Gleitkomma-Rauschen.
- Der TCP-Port wurde als Kommazahl gespeichert (`8899.0`) und landete so in der Unique-ID.

### Intern

- CI mit pytest und ruff, Dependabot, Home-Assistant-Integrationstests.

## 0.3.0

Vorherige Version (Stand der Erstveröffentlichung im Repository).

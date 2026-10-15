# Changelog

## 0.4.0 (unveröffentlicht)

### Achtung beim Update

- **Gerätetyp** und **Regenerationsschritt** sind jetzt Enum-Sensoren. Der
  Zustand ist ein Schlüssel (`type_12`, `step_0`), die Anzeige wird übersetzt.
  Automationen oder Templates, die auf die bisherigen deutschen Texte prüfen,
  müssen angepasst werden. Unbekannte Werte liefern keinen Zustand mehr.
- Die **Sensorklassen** haben sich geändert: Wasserverbrauch 24 h sowie Soll-
  und Restkapazität sind reine Messwerte ohne Wasser-Geräteklasse.
  Der Spitzendurchfluss nutzt die Geräteklasse Durchflussrate.
- TCP-Einträge werden automatisch migriert (Unique-ID ohne `.0` am Port).

### Neu

- Sensoren „Restkapazität Säule 1/2 (Prozent)“ und Binärsensor
  „Regeneration aktiv“.
- Der Regenerationsschritt wird schneller abgefragt (Standard 15 s) als die
  übrigen Werte (Standard 60 s); beide Intervalle sind einstellbar.
- Dropdown für erkannte serielle Ports; Dokumentation für ser2net.
- Verbindung (Port, Host, TCP-Port) lässt sich neu konfigurieren.
- Diagnose-Download mit geschwärzter Konfiguration, Werten und Roh-Frames.
- Sensoren werden nur für Werte angelegt, die das Gerät tatsächlich meldet.
- Das Gerät heißt wie der Konfigurationseintrag.

### Behoben

- Antworten auf einen anderen Befehl (Echo, verspätete oder fremde Antworten
  bei zweitem Client) brechen den Poll nicht mehr ab.
- Einzelne fehlgeschlagene Befehle machen nicht mehr alle Sensoren
  „nicht verfügbar“; Werte verfallen erst nach drei verpassten Abfragen.
- Skalierte Werte (Salzverbrauch) ohne Gleitkomma-Rauschen.

### Intern

- CI mit pytest und ruff, Dependabot, Home-Assistant-Integrationstests.

## 0.3.0

Erste veröffentlichte Version.

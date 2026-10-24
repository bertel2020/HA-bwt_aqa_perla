# Änderungsprotokoll

*[🇬🇧 English version](CHANGELOG.en.md)*

Alle nennenswerten Änderungen an diesem Projekt werden hier dokumentiert.
Versionen folgen dem Feld `version` in
`custom_components/bwt_aqa_perla/manifest.json`.

## Unveröffentlicht

### Neu

- Optionale Diagnosesensoren „Kalenderwoche des Geräts“ (`0x27`) und „Verbrauch 24 h (Höchstwert?)“ (`0x09`), beide standardmäßig deaktiviert; die Bedeutung ist aus der Anzeige von SoftControl abgeleitet.
- Die Pause zwischen zwei Befehlen beträgt 0,2 statt 0,5 s (wie bei SoftControl); eine volle Abfrage dauert damit etwa 3,5 statt 8,5 s.

## 1.1.0 – 2026-10-15

### Achtung beim Update

- **Home Assistant 2026.10 oder neuer** ist erforderlich (Portauswahl von Home Assistant).
- Die Verbindung wird jetzt als ein Wert gespeichert (`serial_port`, bei TCP als `socket://host:port`); die Unique-ID ist die Verbindung selbst. Bestehende Einträge werden automatisch migriert. Die Baudrate gehört jetzt zur Verbindung und wird über **Neu konfigurieren** geändert; die Optionen enthalten nur noch die Abfrageintervalle.
- Die Integration hängt von `usb` ab (wird automatisch geladen).

### Neu

- Einrichtung und Neukonfiguration beginnen mit einem Menü **USB / seriell** oder **Netzwerk (ser2net / TCP)**; die Verbindungsart lässt sich nachträglich wechseln.
- Auswahl des seriellen Ports über die Portauswahl von Home Assistant.
- Diagnosesensoren „Letzte erfolgreiche Abfrage“ und „Fehlgeschlagene Abfragen“.
- Reparaturhinweis, wenn seit über 10 Minuten keine Abfrage erfolgreich war.
- Das Gerät kann in der Oberfläche entfernt werden.

### Intern

- Tests und CI laufen mit Python 3.14 und Home Assistant 2026.10.

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
- Symbole für die Sensoren und ein eigenes Logo für die README.

### Behoben

- Antworten auf einen anderen Befehl (Echo, verspätete oder fremde Antworten bei einem zweiten Client) brechen den Poll nicht mehr ab.
- Einzelne fehlgeschlagene Befehle machen nicht mehr alle Sensoren „nicht verfügbar“; Werte verfallen erst nach drei verpassten Abfragen.
- Skalierte Werte (Salzverbrauch) ohne Gleitkomma-Rauschen.
- Der TCP-Port wurde als Kommazahl gespeichert (`8899.0`) und landete so in der Unique-ID.

### Intern

- CI mit pytest und ruff, Dependabot, Home-Assistant-Integrationstests.

## 0.3.0

Vorherige Version (Stand der Erstveröffentlichung im Repository).

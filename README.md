# BWT AQA Perla für Home Assistant

[![Validate](https://github.com/bertel2020/HA-bwt_aqa_perla/actions/workflows/validate.yml/badge.svg)](https://github.com/bertel2020/HA-bwt_aqa_perla/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Lokale Home-Assistant-Custom-Integration für eine ältere BWT AQA Perla mit
USB-/UART-Verbindung oder einer transparenten Serial-over-TCP-Bridge. Es findet
keine Cloud-Kommunikation statt.

## Installation

### Über HACS

[![Repository in HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bertel2020&repository=HA-bwt_aqa_perla&category=integration)

Das Repository über den Button als benutzerdefiniertes Integrations-Repository
hinzufügen, **BWT AQA Perla** in HACS installieren und Home Assistant neu
starten.

### Manuell

1. Den Ordner `custom_components/bwt_aqa_perla` nach
   `/config/custom_components/bwt_aqa_perla` in Home Assistant kopieren.
2. Home Assistant neu starten.

### Integration einrichten

[![Integration zu Home Assistant hinzufügen](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=bwt_aqa_perla)

Alternativ **Einstellungen → Geräte & Dienste → Integration hinzufügen → BWT
AQA Perla** öffnen. Verbindung auswählen und den Assistenten abschließen. Der
Assistent liest vor dem Speichern testweise den 24-h-Verbrauch.

Für USB sollte nach Möglichkeit ein stabiler Pfad wie
`/dev/serial/by-id/...` statt `/dev/ttyUSB0` verwendet werden. Bei Home
Assistant Container muss das USB-Gerät in den Container durchgereicht sein.

Die Serial-over-TCP-Variante erwartet eine **transparente Raw-TCP-Verbindung**.
Die Bridge muss Baudrate, 8 Datenbits, keine Parität und 1 Stoppbit selbst am
seriellen Anschluss einstellen. Telnet-, RFC2217-, HTTP- und Modbus-TCP-Gateways
sind nicht gemeint.

## Wichtige Konfigurationsannahme

Die vorhandene Anlagenkonfiguration verwendet `9600 Baud, 8 Datenbits, keine
Parität, 1 Stoppbit` (`9600 8N1`). Diese Werte sind deshalb die Vorgabe der
Integration. Abweichende Geräte können 19200 Baud verwenden; maßgeblich ist die
Konfiguration der konkreten Anlage.

## Bereitgestellte Sensoren

| Befehl | Sensor | Nutzdaten | Auswertung |
|---:|---|---:|---|
| `0x08` | Wasserverbrauch 24 h | 2 Byte | unsigned little-endian, Liter |
| `0x10` | Wasserverbrauch gesamt | 4 Byte | unsigned little-endian, Liter |
| `0x13` | Salzverbrauch gesamt | 4 Byte | unsigned little-endian, geteilt durch 1000, kg |
| `0x25` | Sollkapazität Säule 1 | 2 Byte | unsigned little-endian, Liter |
| `0x26` | Sollkapazität Säule 2 | 2 Byte | unsigned little-endian, Liter |
| `0x02` | Restkapazität Säule 1 | 2 Byte | unsigned little-endian, Liter |
| `0x03` | Restkapazität Säule 2 | 2 Byte | unsigned little-endian, Liter |
| `0x11` | Regenerationen | 2 Byte | unsigned little-endian |
| `0x04` | Regenerationsschritt | 1 Byte | `raw & 0x7F`; Klartext plus Rohwert-/Flag-Attribute |
| `0x14` | Regeneriermitteleinsparung | 2 Byte | unsigned little-endian, Rohwert |
| `0x01` | Gerätetyp | 1 Byte | Gerätetypcode; `12` = Aqua Perla |
| `0x05` | Spitzendurchfluss heute | 2 Byte | unsigned little-endian, l/h |
| `0x06` | Spitzendurchfluss 24 h | 2 Byte | unsigned little-endian, l/h |
| `0x07` | Spitzendurchfluss seit Inbetriebnahme | 2 Byte | unsigned little-endian, l/h |
| `0x12` | Regenerationen seit Service | 2 Byte | unsigned little-endian |
| `0x15` | Inbetriebnahmedatum | variabel | ASCII-Text |
| `0x19` | Softwareversionen | variabel | Leistungselektronik und Bedienteil getrennt |

Die Diagnosebefehle sind optional, damit abweichende Firmwarestände die
Kernmesswerte nicht blockieren. Die Einheit von Befehl `0x14` ist nicht
abschließend geklärt. Der Wert bleibt deshalb ein optionaler Rohwert: Eine
fehlende oder abweichende Antwort setzt nur diesen Sensor auf „nicht verfügbar“,
nicht das gesamte Gerät.

Beim Regenerationsschritt wird Bit 7 für die Textzuordnung ausgeblendet, bleibt
aber zusammen mit dem originalen Byte als Entitätsattribut sichtbar.
Eine Antwort wie `Version: 3.94#155` wird zusätzlich in die Diagnosesensoren
„Softwareversion Leistungselektronik“ (`3.94`) und „Softwareversion Bedienteil“
(`155`) aufgeteilt.

## Kommunikation

Die Implementierung liest längencodierte Frames vollständig ein, validiert
Grenzen, Befehl und Prüfsumme und führt alle Abfragen nacheinander aus. Nach
jedem Poll wird die Verbindung geordnet geschlossen und beim nächsten Poll neu
aufgebaut. Das reduziert das Risiko festgefahrener USB- oder
Serial-over-TCP-Sitzungen.

Home Assistant protokolliert Kommunikations- und Protokollfehler unter
`custom_components.bwt_aqa_perla`.

Baudrate und Abfrageintervall lassen sich nach der Einrichtung unter
**Einstellungen → Geräte & Dienste → BWT AQA Perla → Konfigurieren** ändern.
Bei Serial over TCP muss die Baudrate direkt an der Bridge eingestellt werden.

Die Integration enthält das aktuelle BWT-Markenlogo und das quadratische
BWT-Appsymbol im von Home Assistant unterstützten lokalen `brand/`-Verzeichnis.
Die Markenrechte verbleiben bei BWT.

> **Markenhinweis:** Dieses Projekt ist eine unabhängige, inoffizielle
> Integration und steht in keiner Verbindung zu BWT Holding GmbH oder BWT
> Wassertechnik GmbH. BWT und AQA Perla sind Marken ihrer jeweiligen Inhaber.
> Die Marken und Markenabbildungen sind nicht Bestandteil der
> Open-Source-Lizenz dieses Projekts.

# BWT AQA Perla für Home Assistant

[![Validate](https://github.com/bertel2020/HA-bwt_aqa_perla/actions/workflows/validate.yml/badge.svg)](https://github.com/bertel2020/HA-bwt_aqa_perla/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/bertel2020/HA-bwt_aqa_perla)](https://github.com/bertel2020/HA-bwt_aqa_perla/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Lizenz: MIT](https://img.shields.io/github/license/bertel2020/HA-bwt_aqa_perla)](LICENSE)

Lokale Home-Assistant-Custom-Integration für eine ältere **BWT AQA Perla**
(Doppelsäulen-Enthärtungsanlage) mit USB-/UART-Verbindung oder einer
transparenten Serial-over-TCP-Bridge. Es findet keine Cloud-Kommunikation
statt; die Anlage wird ausschließlich lesend abgefragt.

## Funktionen

- Wasser-, Salz- und Regenerationsdaten der Anlage als Sensoren, geeignet für
  das Energie-/Wasser-Dashboard und die Langzeitstatistik
- Restkapazität pro Säule in Liter und in Prozent
- Aktueller Regenerationsschritt im Klartext (deutsch und englisch) und
  Binärsensor „Regeneration aktiv“
- Schnellere Abfrage des Regenerationsschritts als der übrigen Werte
- Direkte serielle Verbindung (mit Port-Auswahl) oder Serial over TCP
  (z. B. ser2net)
- Robust bei Teilausfällen: ein fehlender Wert macht nicht alle Sensoren
  „nicht verfügbar“
- Einrichtung, Optionen und Neukonfiguration vollständig über die Oberfläche
- Diagnose-Download für die Fehlersuche
- Deutsche und englische Oberfläche

## Voraussetzungen

- Home Assistant 2026.2 oder neuer (gegen diese Version getestet; ältere Versionen sind nicht geprüft)
- Eine BWT AQA Perla mit serieller Schnittstelle, angebunden über
  - einen USB-Seriell-/UART-Adapter an dem Rechner, auf dem Home Assistant
    läuft, **oder**
  - eine transparente Raw-TCP-Bridge (ser2net, ESP-/RS232-Ethernet-Gateway
    o. Ä.)
- Zugriff auf die Schnittstelle durch **genau einen** Client gleichzeitig
  (siehe [Fehlersuche](#fehlersuche))

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

## Einrichtung

[![Integration zu Home Assistant hinzufügen](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=bwt_aqa_perla)

Alternativ **Einstellungen → Geräte & Dienste → Integration hinzufügen → BWT
AQA Perla** öffnen. Verbindung auswählen und den Assistenten abschließen. Der
Assistent liest vor dem Speichern testweise den 24-h-Verbrauch.

### USB / seriell

Im Assistenten werden erkannte serielle Ports als Auswahl angeboten (stabile
`/dev/serial/by-id/...`-Pfade zuerst); ein eigener Pfad kann weiterhin
eingetragen werden. Nach Möglichkeit sollte ein stabiler Pfad statt
`/dev/ttyUSB0` verwendet werden. Bei Home Assistant Container muss das
USB-Gerät in den Container durchgereicht sein.

Die Anlage verwendet in der Regel `9600 Baud, 8 Datenbits, keine Parität,
1 Stoppbit` (`9600 8N1`); das ist die Vorgabe der Integration. Abweichende
Geräte können 19200 Baud verwenden – maßgeblich ist die Konfiguration der
konkreten Anlage.

### Serial over TCP

Die Variante erwartet eine **transparente Raw-TCP-Verbindung**. Die Bridge muss
Baudrate, 8 Datenbits, keine Parität und 1 Stoppbit selbst am seriellen
Anschluss einstellen. Telnet-, RFC2217-, HTTP- und Modbus-TCP-Gateways sind
nicht gemeint.

#### Beispiel: ser2net

Auf einem Rechner mit angeschlossenem Adapter (z. B. Raspberry Pi) stellt
[ser2net](https://github.com/cminyard/ser2net) den seriellen Port als Raw-TCP
bereit. Beispiel für `/etc/ser2net.yaml` (ser2net 4.x):

```yaml
%YAML 1.1
---
connection: &bwt-aqa-perla
  accepter: tcp,8899
  enable: on
  connector: serialdev,/dev/serial/by-id/usb-XXXX,9600n81,local
```

Bei ser2net 3.x lautet die entsprechende Zeile in `/etc/ser2net.conf`:

```
8899:raw:0:/dev/serial/by-id/usb-XXXX:9600 8DATABITS NONE 1STOPBIT
```

In der Integration **Serial over TCP** wählen, den Host des Rechners und den
Port `8899` eintragen. Die Baudrate (`9600n81`) wird ausschließlich in ser2net
eingestellt. Der Accepter `tcp` ist roh; `telnet(rfc2217)` oder `telnet` dürfen
**nicht** verwendet werden.

## Konfiguration

Unter **Einstellungen → Geräte & Dienste → BWT AQA Perla → Konfigurieren**:

| Option | Standard | Bereich | Bedeutung |
|---|---:|---|---|
| Abfrageintervall | 60 s | 30–3600 s | Intervall für alle Werte außer dem Regenerationsschritt |
| Abfrageintervall Regeneration | 15 s | 5–3600 s | Intervall für den Regenerationsschritt |
| Baudrate | 9600 | 1200–56000 | nur bei direkter serieller Verbindung |

Bei Serial over TCP muss die Baudrate direkt an der Bridge eingestellt werden.
Seriellen Port bzw. Host und TCP-Port ändert man über das Menü der Integration
(⋮) unter **Neu konfigurieren**, ohne die Integration neu anzulegen. Änderungen
laden die Integration automatisch neu.

## Entitäten

Die Entity-IDs hängen vom Namen des Geräts ab (Standard: Titel des Eintrags).

### Wasser und Salz

| Entität | Einheit | Hinweis |
|---|---|---|
| Wasserverbrauch 24 h | L | gleitender Wert der letzten 24 Stunden |
| Wasserverbrauch gesamt | L | steigender Zähler, für das Wasser-Dashboard geeignet |
| Salzverbrauch gesamt | kg | steigender Zähler |
| Spitzendurchfluss heute / 24 h / seit Inbetriebnahme | L/h | optional |

### Säulen und Regeneration

| Entität | Einheit | Hinweis |
|---|---|---|
| Sollkapazität Säule 1 / 2 | L | |
| Restkapazität Säule 1 / 2 | L | |
| Restkapazität Säule 1 / 2 (Prozent) | % | berechnet; entfällt bei ungenutzter Säule |
| Regenerationen | – | steigender Zähler |
| Regenerationen seit Service | – | optional |
| Regenerationsschritt | – | Klartext; Attribute `raw_value`, `normalized_step`, `flag_bit_7`, `short_code` |
| Regeneration aktiv | – | Binärsensor, an solange der Schritt nicht „Säulen in Betrieb“ ist |
| Regeneriermitteleinsparung | Rohwert | optional; Einheit nicht abschließend geklärt |

### Diagnose

Gerätetyp (z. B. „Aqua Perla“), Inbetriebnahmedatum sowie die Softwareversionen
von Leistungselektronik und Bedienteil (eine Antwort wie `Version: 3.94#155`
wird in `3.94` und `155` aufgeteilt). Die kombinierte Softwareversion ist
standardmäßig deaktiviert.

Optionale Werte werden nur angelegt, wenn die Anlage sie meldet. Die
Zustände von **Gerätetyp** und **Regenerationsschritt** sind Schlüssel
(`type_12`, `step_0`), die Oberfläche zeigt die übersetzte Bezeichnung.
Automationen sollten deshalb auf diese Schlüssel prüfen oder den Binärsensor
„Regeneration aktiv“ verwenden.

Liter-Werte werden standardmäßig ohne Nachkommastellen angezeigt, der
Salzverbrauch mit zwei. Das lässt sich pro Entität unter **Anzeigegenauigkeit**
ändern.

## Beispiele

Benachrichtigung bei Beginn einer Regeneration (Entity-ID gegebenenfalls
anpassen):

```yaml
automation:
  - alias: BWT Regeneration gestartet
    triggers:
      - trigger: state
        entity_id: binary_sensor.bwt_aqa_perla_regeneration_aktiv
        from: "off"
        to: "on"
    actions:
      - action: notify.notify
        data:
          message: "Die Enthärtungsanlage regeneriert."
```

Warnung bei niedriger Restkapazität:

```yaml
automation:
  - alias: BWT Restkapazität niedrig
    triggers:
      - trigger: numeric_state
        entity_id: sensor.bwt_aqa_perla_restkapazitat_saule_1_prozent
        below: 10
    actions:
      - action: notify.notify
        data:
          message: "Restkapazität Säule 1 unter 10 %."
```

## Fehlersuche

**Alle Sensoren sind kurz „nicht verfügbar“ oder es erscheinen
`Expected command`-Fehler im Log.** Greift gleichzeitig ein zweites System auf
dieselbe serielle Leitung oder Bridge zu (etwa IP-Symcon oder SoftControl),
vermischen sich die Antworten. Die Integration überspringt fremde Antworten,
sauber ist aber nur ein einziger aktiver Client. Die Integration baut pro Poll
eine neue Verbindung auf; bei Bridges, die nur eine Verbindung erlauben, kann
das einen anderen Client verdrängen.

**Verbindung schlägt fehl.** Host, Port und Baudrate prüfen. Bei ser2net muss
der Accepter `tcp` (roh) sein, nicht `telnet`. Bei USB prüfen, ob das Gerät im
Container ankommt und Home Assistant Zugriff auf den Port hat.

**Einzelne Sensoren fehlen.** Optionale Werte werden nur angelegt, wenn die
Anlage sie beantwortet; ältere Firmwarestände unterstützen nicht alle Befehle.

**Debug-Protokoll.** In `configuration.yaml` aktivieren:

```yaml
logger:
  logs:
    custom_components.bwt_aqa_perla: debug
```

**Diagnose herunterladen.** Unter **Einstellungen → Geräte & Dienste → BWT AQA
Perla → ⋮ → Diagnose herunterladen** liegt die (geschwärzte) Konfiguration, die
dekodierten Werte und je Befehl der zuletzt empfangene Roh-Frame. Bitte bei
Problemberichten anhängen.

Fehler und Wünsche bitte als
[Issue](https://github.com/bertel2020/HA-bwt_aqa_perla/issues) melden.

## Funktionsweise

Die Anlage wird über ein einfaches Telegrammprotokoll abgefragt:

```
0x0D | Befehl | Länge | Nutzdaten | Prüfsumme | 0x0A
```

Die Prüfsumme ist die Summe aller vorangehenden Bytes modulo 256, Mehrbyte-Werte
sind little-endian. Die Implementierung liest längencodierte Frames vollständig
ein, validiert Grenzen, Befehl und Prüfsumme und führt alle Abfragen
nacheinander aus. Antworten auf einen anderen Befehl (Echo, verspätete oder
fremde Antworten) werden übersprungen. Das Protokoll wurde aus öffentlich
verfügbaren Telegrammmitschnitten und IP-Symcon-Skripten abgeleitet; es gibt
keine Herstellerdokumentation.

Schlägt eine einzelne Abfrage fehl, behalten die übrigen Sensoren ihren Wert;
ein fehlender Wert bleibt erhalten und wird erst nach drei verpassten
Abfragen „nicht verfügbar“. Nach jedem Poll wird die Verbindung geordnet
geschlossen und beim nächsten Poll neu aufgebaut. Das reduziert das Risiko
festgefahrener USB- oder Serial-over-TCP-Sitzungen.

| Befehl | Wert | Nutzdaten | Auswertung |
|---:|---|---:|---|
| `0x08` | Wasserverbrauch 24 h | 2 Byte | unsigned, Liter |
| `0x10` | Wasserverbrauch gesamt | 4 Byte | unsigned, Liter |
| `0x13` | Salzverbrauch gesamt | 4 Byte | unsigned, geteilt durch 1000, kg |
| `0x25` / `0x26` | Sollkapazität Säule 1 / 2 | 2 Byte | unsigned, Liter |
| `0x02` / `0x03` | Restkapazität Säule 1 / 2 | 2 Byte | unsigned, Liter |
| `0x11` | Regenerationen | 2 Byte | unsigned |
| `0x04` | Regenerationsschritt | 1 Byte | `raw & 0x7F`; Rohwert und Bit 7 als Attribute |
| `0x14` | Regeneriermitteleinsparung | 2 Byte | unsigned, Rohwert (optional) |
| `0x01` | Gerätetyp | 1 Byte | Gerätetypcode; `12` = Aqua Perla (optional) |
| `0x05` / `0x06` / `0x07` | Spitzendurchfluss heute / 24 h / gesamt | 2 Byte | unsigned, L/h (optional) |
| `0x12` | Regenerationen seit Service | 2 Byte | unsigned (optional) |
| `0x15` | Inbetriebnahmedatum | variabel | ASCII (optional) |
| `0x19` | Softwareversionen | variabel | ASCII (optional) |

## Entwicklung

Voraussetzung ist Python 3.13.

```bash
pip install -r requirements_test.txt
ruff check . && ruff format --check .
pytest
```

Die Tests laufen ohne Gerät; die Home-Assistant-Tests nutzen einen
Fake-Client. Beiträge sind willkommen: bitte Tests ergänzen und `ruff` sauber
halten. Änderungen stehen im [Changelog](CHANGELOG.md).

## Lizenz und Hinweise

Der Quellcode steht unter der [MIT-Lizenz](LICENSE).

Die Integration enthält das aktuelle BWT-Markenlogo und das quadratische
BWT-Appsymbol im von Home Assistant unterstützten lokalen `brand/`-Verzeichnis.
Die Markenrechte verbleiben bei BWT.

> **Markenhinweis:** Dieses Projekt ist eine unabhängige, inoffizielle
> Integration und steht in keiner Verbindung zu BWT Holding GmbH oder BWT
> Wassertechnik GmbH. BWT und AQA Perla sind Marken ihrer jeweiligen Inhaber.
> Die Marken und Markenabbildungen sind nicht Bestandteil der
> Open-Source-Lizenz dieses Projekts.

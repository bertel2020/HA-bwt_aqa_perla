<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/bertel2020/HA-bwt_aqa_perla/main/assets/logo_dark.png">
    <img src="https://raw.githubusercontent.com/bertel2020/HA-bwt_aqa_perla/main/assets/logo.png" alt="BWT AQA Perla" width="320">
  </picture>
</p>

<h1 align="center">BWT AQA Perla</h1>

<p align="center">
  Home-Assistant-Integration für die BWT AQA Perla – lokal per USB/seriell oder Serial over TCP, komplett über die Oberfläche einrichtbar.
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://www.home-assistant.io/"><img src="https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-18BCF2.svg?logo=home-assistant&logoColor=white" alt="Home Assistant"></a>
  <a href="https://github.com/bertel2020/HA-bwt_aqa_perla/releases"><img src="https://img.shields.io/github/v/release/bertel2020/HA-bwt_aqa_perla?sort=semver&include_prereleases" alt="Release"></a>
  <a href="https://github.com/bertel2020/HA-bwt_aqa_perla/actions/workflows/validate.yml"><img src="https://github.com/bertel2020/HA-bwt_aqa_perla/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/bertel2020/HA-bwt_aqa_perla" alt="LICENSE"></a>
</p>

<p align="center">
  <a href="https://buymeacoffee.com/bertel2020"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-FFDD00?logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee"></a>
  <a href="https://ko-fi.com/bertel2020"><img src="https://img.shields.io/badge/Ko--fi-support-FF5E5B?logo=ko-fi&logoColor=white" alt="Ko-fi"></a>
  <a href="https://paypal.me/RobertoMartins"><img src="https://img.shields.io/badge/PayPal-donate-00457C?logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

<p align="center"><em><a href="README.en.md">🇬🇧 English version</a></em></p>

Eine über die Oberfläche konfigurierbare Home-Assistant-Custom-Integration für die ältere **BWT AQA Perla** (Doppelsäulen-Enthärtungsanlage). Sie liest Wasser-, Salz- und Regenerationsdaten über die serielle Schnittstelle der Anlage und stellt sie als Sensoren bereit. Es findet keine Cloud-Kommunikation statt, und die Anlage wird ausschließlich lesend abgefragt.

## Funktionen

- Wasser-, Salz- und Regenerationsdaten als Sensoren, geeignet für das Wasser-Dashboard und die Langzeitstatistik
- Restkapazität pro Säule in Litern und in Prozent
- Aktueller Regenerationsschritt im Klartext (deutsch/englisch) und Binärsensor „Regeneration aktiv“
- Schnellere Abfrage des Regenerationsschritts als der übrigen Werte
- Direkte serielle Verbindung (mit Port-Auswahl) oder Serial over TCP (z. B. ser2net)
- Robust bei Teilausfällen: ein fehlender Wert macht nicht alle Sensoren „nicht verfügbar“
- Einrichtung, Optionen und Neukonfiguration vollständig über die Oberfläche
- Diagnose-Download für die Fehlersuche

## Voraussetzungen

- Home Assistant **2026.10** oder neuer (Auswahl des seriellen Ports und Neukonfiguration).
- Eine BWT AQA Perla mit serieller Schnittstelle, angebunden über einen USB-Seriell-/UART-Adapter am Rechner von Home Assistant **oder** eine transparente Raw-TCP-Bridge (ser2net, RS232-Ethernet-Gateway o. Ä.).
- Zugriff auf die Schnittstelle durch **genau einen** Client gleichzeitig (siehe [Fehlersuche](#fehlersuche)).

## Installation

### Über HACS (empfohlen)

[![HACS-Repository in My Home Assistant öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bertel2020&repository=HA-bwt_aqa_perla&category=integration)
[![BWT AQA Perla zu My Home Assistant hinzufügen](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=bwt_aqa_perla)

1. Über den ersten Button das Repository in HACS öffnen.
2. **BWT AQA Perla** herunterladen und Home Assistant neu starten.
3. Über den zweiten Button die Integration hinzufügen. Alternativ in Home Assistant **Einstellungen → Geräte & Dienste → Integration hinzufügen → BWT AQA Perla** öffnen.

Falls der erste Button nicht funktioniert, in HACS unter **Integrationen → Benutzerdefinierte Repositories** `https://github.com/bertel2020/HA-bwt_aqa_perla` als Kategorie **Integration** eintragen.

### Manuell

Das Verzeichnis `custom_components/bwt_aqa_perla` nach `/config/custom_components/bwt_aqa_perla` kopieren und Home Assistant neu starten.

## Einrichtung

Einstellungen → Geräte & Dienste → Integration hinzufügen → **BWT AQA Perla**. Der Assistent liest vor dem Speichern testweise den 24-h-Verbrauch.

1. Im Menü **USB / seriell** oder **Netzwerk (ser2net / TCP)** wählen.
   - USB / seriell: Port aus der Liste wählen, Baudrate (Standard `9600`).
   - Netzwerk: Host/IP und Raw-TCP-Port (Standard `8899`).
2. Die Abfrageintervalle (Standard 60 s und 15 s für den Regenerationsschritt) lassen sich danach über **Konfigurieren** ändern.

### USB / seriell

Der Assistent verwendet die Portauswahl von Home Assistant (die `usb`-Integration wird automatisch mitgeladen). Nach Möglichkeit sollte ein stabiler Pfad `/dev/serial/by-id/...` statt `/dev/ttyUSB0` gewählt werden. Bei Home Assistant Container muss das USB-Gerät in den Container durchgereicht sein.

Die Anlage verwendet in der Regel `9600 Baud, 8 Datenbits, keine Parität, 1 Stoppbit` (`9600 8N1`); das ist die Vorgabe der Integration. Abweichende Geräte können 19200 Baud verwenden – maßgeblich ist die Konfiguration der konkreten Anlage.

### Serial over TCP (ser2net)

Die Variante erwartet eine **transparente Raw-TCP-Verbindung**. Die Bridge muss Baudrate, 8 Datenbits, keine Parität und 1 Stoppbit selbst am seriellen Anschluss einstellen. Telnet-, RFC2217-, HTTP- und Modbus-TCP-Gateways sind nicht gemeint.

Auf einem Rechner mit angeschlossenem Adapter (z. B. Raspberry Pi) stellt [ser2net](https://github.com/cminyard/ser2net) den seriellen Port als Raw-TCP bereit. Beispiel für `/etc/ser2net.yaml` (ser2net 4.x):

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

In der Integration **Netzwerk (ser2net / TCP)** wählen, den Host des Rechners und den Port `8899` eintragen. Die Baudrate (`9600n81`) wird ausschließlich in ser2net eingestellt. Der Accepter `tcp` ist roh; `telnet(rfc2217)` oder `telnet` dürfen **nicht** verwendet werden.

## Konfiguration (Optionen)

Über den **Konfigurieren**-Button der Integration:

| Option | Standard | Bereich | Bedeutung |
|---|---:|---|---|
| Abfrageintervall | 60 s | 30–3600 s | Intervall für alle Werte außer dem Regenerationsschritt |
| Abfrageintervall Regeneration | 15 s | 5–3600 s | Intervall für den Regenerationsschritt |

Änderungen laden die Integration automatisch neu.

**Verbindung ändern:** Port und Baudrate bzw. Host und TCP-Port (auch die Verbindungsart, z. B. von USB auf Netzwerk) ändert man über das Menü der Integration (⋮) unter **Neu konfigurieren**, ohne die Integration neu anzulegen. Bei ser2net und anderen Bridges wird die Baudrate an der Bridge selbst eingestellt.

## Entities

Es wird ein Gerät **„BWT AQA Perla“** angelegt (bei Serial over TCP mit dem Host im Titel). Optionale Werte werden nur angelegt, wenn die Anlage sie beantwortet; ältere Firmwarestände unterstützen nicht alle Befehle.

Die Entity-ID entsteht aus Gerätename + Entity-Name (Home Assistants Standard-Schema bei `has_entity_name`). Home Assistant vergibt sie **einmalig bei der Ersteinrichtung** und richtet sie nach der **zu diesem Zeitpunkt aktiven Sprache der Oberfläche**; die Tabelle zeigt die deutschen Namen. Bei einer anderen Sprache oder einem anderen Gerätenamen weichen die tatsächlichen IDs ab – maßgeblich ist, was **Einstellungen → Geräte & Dienste → BWT AQA Perla** anzeigt.

| Friendly Name | Entity-ID | Befehl | Beschreibung |
|---|---|---|---|
| Wasserverbrauch 24 h | `sensor.bwt_aqa_perla_wasserverbrauch_24_h` | `0x08` | Wasserverbrauch der letzten 24 Stunden (gleitender Wert) |
| Verbrauch 24 h (Höchstwert?) | `sensor.bwt_aqa_perla_verbrauch_24_h_hochstwert` | `0x09` | Vermutlich der höchste 24-h-Verbrauch seit Inbetriebnahme (aus SoftControl abgeleitet); Diagnose, optional, standardmäßig deaktiviert |
| Wasserverbrauch gesamt | `sensor.bwt_aqa_perla_wasserverbrauch_gesamt` | `0x10` | Steigender Gesamtzähler, geeignet für das Wasser-Dashboard |
| Salzverbrauch gesamt | `sensor.bwt_aqa_perla_salzverbrauch_gesamt` | `0x13` | Steigender Gesamtzähler in kg (Rohwert geteilt durch 1000) |
| Spitzendurchfluss heute | `sensor.bwt_aqa_perla_spitzendurchfluss_heute` | `0x05` | Spitzendurchfluss heute; optional |
| Spitzendurchfluss 24 h | `sensor.bwt_aqa_perla_spitzendurchfluss_24_h` | `0x06` | Spitzendurchfluss der letzten 24 Stunden; optional |
| Spitzendurchfluss seit Inbetriebnahme | `sensor.bwt_aqa_perla_spitzendurchfluss_seit_inbetriebnahme` | `0x07` | Spitzendurchfluss seit Inbetriebnahme; optional |
| Sollkapazität Säule 1 | `sensor.bwt_aqa_perla_sollkapazitat_saule_1` | `0x25` | Sollkapazität der Säule 1 in Litern |
| Sollkapazität Säule 2 | `sensor.bwt_aqa_perla_sollkapazitat_saule_2` | `0x26` | Sollkapazität der Säule 2 in Litern |
| Restkapazität Säule 1 | `sensor.bwt_aqa_perla_restkapazitat_saule_1` | `0x02` | Restkapazität der Säule 1 in Litern |
| Restkapazität Säule 2 | `sensor.bwt_aqa_perla_restkapazitat_saule_2` | `0x03` | Restkapazität der Säule 2 in Litern |
| Restkapazität Säule 1 (Prozent) | `sensor.bwt_aqa_perla_restkapazitat_saule_1_prozent` | berechnet | Rest- durch Sollkapazität; nur bei genutzter Säule |
| Restkapazität Säule 2 (Prozent) | `sensor.bwt_aqa_perla_restkapazitat_saule_2_prozent` | berechnet | Rest- durch Sollkapazität; nur bei genutzter Säule |
| Regenerationen | `sensor.bwt_aqa_perla_regenerationen` | `0x11` | Steigender Zähler der Regenerationen |
| Regenerationen seit Service | `sensor.bwt_aqa_perla_regenerationen_seit_service` | `0x12` | Regenerationen seit dem letzten Service; optional |
| Regenerationsschritt | `sensor.bwt_aqa_perla_regenerationsschritt` | `0x04` | Aktueller Schritt im Klartext; Attribute `raw_value`, `normalized_step`, `flag_bit_7`, `short_code` |
| Regeneriermitteleinsparung | `sensor.bwt_aqa_perla_regeneriermitteleinsparung` | `0x14` | Rohwert, Einheit nicht abschließend geklärt; optional |
| Regeneration aktiv | `binary_sensor.bwt_aqa_perla_regeneration_aktiv` | abgeleitet | An, solange der Schritt nicht „Säulen in Betrieb“ ist |
| Gerätetyp | `sensor.bwt_aqa_perla_geratetyp` | `0x01` | Gerätetyp, z. B. „Aqua Perla“; Diagnose, optional |
| Inbetriebnahmedatum | `sensor.bwt_aqa_perla_inbetriebnahmedatum` | `0x15` | Inbetriebnahmedatum; Diagnose, optional |
| Softwareversion Leistungselektronik | `sensor.bwt_aqa_perla_softwareversion_leistungselektronik` | `0x19` | Version der Leistungselektronik, z. B. `3.94`; Diagnose |
| Softwareversion Bedienteil | `sensor.bwt_aqa_perla_softwareversion_bedienteil` | `0x19` | Version des Bedienteils, z. B. `155`; Diagnose |
| Letzte erfolgreiche Abfrage | `sensor.bwt_aqa_perla_letzte_erfolgreiche_abfrage` | – | Zeitpunkt der letzten erfolgreichen Abfrage; Diagnose, bleibt auch bei Ausfall verfügbar |
| Fehlgeschlagene Abfragen | `sensor.bwt_aqa_perla_fehlgeschlagene_abfragen` | – | Anzahl fehlgeschlagener Abfragen seit dem Start; Diagnose |
| Kalenderwoche des Geräts | `sensor.bwt_aqa_perla_kalenderwoche_des_gerats` | `0x27` | Vermutlich die Kalenderwoche des Geräts (zeigt eine falsch gehende Geräteuhr); Diagnose, optional, standardmäßig deaktiviert |
| Softwareversion kombiniert | `sensor.bwt_aqa_perla_softwareversion_kombiniert` | `0x19` | Kombinierte Antwort, z. B. `3.94#155`; Diagnose, standardmäßig deaktiviert |

Die Zustände von **Gerätetyp** und **Regenerationsschritt** sind Schlüssel (`type_12`, `step_0`), die Oberfläche zeigt die übersetzte Bezeichnung. Automationen sollten deshalb auf diese Schlüssel prüfen oder den Binärsensor „Regeneration aktiv“ verwenden.

Liter-Werte werden standardmäßig ohne Nachkommastellen angezeigt, der Salzverbrauch mit zwei. Das lässt sich pro Entity unter **Anzeigegenauigkeit** ändern.

## Beispiele

Benachrichtigung bei Beginn einer Regeneration (Entity-ID gegebenenfalls anpassen):

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

**Alle Sensoren sind kurz „nicht verfügbar“ oder es erscheinen `Expected command`-Fehler im Log.** Greift gleichzeitig ein zweites System auf dieselbe serielle Leitung oder Bridge zu (etwa IP-Symcon oder SoftControl), vermischen sich die Antworten. Die Integration überspringt fremde Antworten, sauber ist aber nur ein einziger aktiver Client. Die Integration baut pro Poll eine neue Verbindung auf; bei Bridges, die nur eine Verbindung erlauben, kann das einen anderen Client verdrängen.

**Verbindung schlägt fehl.** Host, Port und Baudrate prüfen. Bei ser2net muss der Accepter `tcp` (roh) sein, nicht `telnet`. Bei USB prüfen, ob das Gerät im Container ankommt und Home Assistant Zugriff auf den Port hat.

**Einzelne Sensoren fehlen.** Optionale Werte werden nur angelegt, wenn die Anlage sie beantwortet.

**Hinweis „Keine Daten von der BWT AQA Perla“.** Er erscheint unter **Einstellungen → Reparaturen**, wenn seit über 10 Minuten keine Abfrage erfolgreich war, und verschwindet von selbst, sobald wieder Daten ankommen. Die Diagnosesensoren „Letzte erfolgreiche Abfrage“ und „Fehlgeschlagene Abfragen“ zeigen, wie stabil die Verbindung ist.

**Debug-Protokoll.** In `configuration.yaml` aktivieren:

```yaml
logger:
  logs:
    custom_components.bwt_aqa_perla: debug
```

**Diagnose herunterladen.** Unter **Einstellungen → Geräte & Dienste → BWT AQA Perla → ⋮ → Diagnose herunterladen** liegen die (geschwärzte) Konfiguration, die dekodierten Werte und je Befehl der zuletzt empfangene Roh-Frame. Bitte bei Problemberichten anhängen.

Fehler und Wünsche bitte als [Issue](https://github.com/bertel2020/HA-bwt_aqa_perla/issues) melden.

## Funktionsweise

Die Anlage wird über ein einfaches Telegrammprotokoll abgefragt:

```
0x0D | Befehl | Länge | Nutzdaten | Prüfsumme | 0x0A
```

Die Prüfsumme ist die Summe aller vorangehenden Bytes modulo 256, Mehrbyte-Werte sind little-endian. Die Implementierung liest längencodierte Frames vollständig ein, validiert Grenzen, Befehl und Prüfsumme und führt alle Abfragen nacheinander aus. Antworten auf einen anderen Befehl (Echo, verspätete oder fremde Antworten) werden übersprungen. Das Protokoll wurde aus öffentlich verfügbaren Telegrammmitschnitten und IP-Symcon-Skripten abgeleitet; eine Herstellerdokumentation gibt es nicht.

Schlägt eine einzelne Abfrage fehl, behalten die übrigen Sensoren ihren Wert; ein fehlender Wert bleibt erhalten und wird erst nach drei verpassten Abfragen „nicht verfügbar“. Nach jedem Poll wird die Verbindung geordnet geschlossen und beim nächsten Poll neu aufgebaut. Das reduziert das Risiko festgefahrener USB- oder Serial-over-TCP-Sitzungen.

Der Regenerationsschritt wird bei Bit 7 maskiert (`raw & 0x7F`); das Bit bleibt zusammen mit dem Originalbyte als Attribut sichtbar. Eine Softwareversion wie `Version: 3.94#155` wird in Leistungselektronik (`3.94`) und Bedienteil (`155`) aufgeteilt.

## Mitwirken

Siehe [CONTRIBUTING.md](CONTRIBUTING.md).

## Änderungsprotokoll

Siehe [CHANGELOG.md](CHANGELOG.md).

## Haftungsausschluss

Dies ist eine unabhängige, community-entwickelte Integration. Sie steht in keiner Verbindung zu BWT und wird von BWT weder unterstützt noch empfohlen. Das Protokoll wurde ohne Herstellerdokumentation aus öffentlich verfügbaren Quellen abgeleitet.

Die Integration liest die Anlage ausschließlich und sendet keine Schreibbefehle. Sie wird **„wie besehen“, ohne jegliche Gewährleistung** bereitgestellt (siehe [LICENSE](LICENSE)) – die Nutzung erfolgt auf eigenes Risiko.

## Markenhinweis

Die Integration enthält das aktuelle BWT-Markenlogo und das quadratische BWT-Appsymbol im von Home Assistant unterstützten lokalen `brand/`-Verzeichnis. „BWT“, „BWT Holding GmbH“, „BWT Wassertechnik GmbH“ und „AQA Perla“ sind Marken ihrer jeweiligen Inhaber; die Markenrechte verbleiben bei BWT. Die Marken und Markenabbildungen sind nicht Bestandteil der Open-Source-Lizenz dieses Projekts. Das Logo in dieser README (`assets/`) ist ein eigener Entwurf und steht unter der Lizenz des Projekts.

## Copyright & Lizenz

Copyright © 2026 bertel2020. Lizenziert unter der [MIT-Lizenz](LICENSE).

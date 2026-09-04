# README
## Start
Voraussetzungen: Fake-API läuft und Abhängigkeiten sind installiert (siehe `README.md` unter `Fake Case API - Setup`).

```bash
# einzelner Tag, über closed_on
python pipeline.py --date 2026-07-14

# Zeitraum, über closed_on 
python pipeline.py --date-from 2026-07-01 --date-to 2026-07-14

# inkrementell, über last_modified
python pipeline.py --since 2026-08-25
```

## Was an den Daten aufgefallen ist
- API liefert überlappende Seiten (letzte 5 Records der Vorseite werden auf der nächsten Seite nochmal mitgeliefert).
- Tokens laufen nach 120 Sekunden ab. Token reicht nicht zwingend bis zum Ende bei Läufen mit vielen Retries oder Seiten.
- Unzuverlässiger Server: 429 (mit `Retry-After`) und 503 (ohne Header) treten regelmäßig auf. 
- Cases haben zum großen Teil ältere Zwischenstände zusätzlich zum aktuellen Stand. Dedup also wichtig. 
- `priority` und `handling_minutes` kommen als String, obwohl sie inhaltlich Zahlen sind.
- `store_no` sieht wie eine Zahl aus, besitzt aber führende Nullen, die bei der Umwandlung in einen Integer für Fehler sorgen würden. 

## Annahmen 
- `store_no`: Besitzt führende Nullen, deshalb keine Transformation zu Integer. Hierbei würden die führenden Nullen verloren gehen und zu falscher Darstellung führen 
- `priority`: `""` und `null` werden zu SQL-`NULL`. `0` wäre ein erfundener Prioritätswert gewesen.
- `handling_minutes`: Werden zu einem Integer gecastet. Negative Werte werden unverändert erhalten. Wichtig wäre, dass wir sie in den Auswertungs-Queries dann bewusst herausfiltern hätten müssen. 
- `category` wird getrimmt und normalisiert. Jede Form von z.B. `"payment "`, `"PAYMENT"`, `"Payment"` wird zu `"Payment"`. Andererseits, würde eine Gruppierung nach Kategorie in zu viele Kategorien zerfallen.
- `created_at`: kommt in zwei Formaten vor (ISO und deutsch). Wird robust gegen beide geparst. 
- `deleted`: Obwohl Fälle existieren, bei denen ein `True` existiert, filtern wir diese nicht ungefragt raus. Allerdings muss das ebenfalls in den Queries berücksichtigt werden. Solche Fälle dürfen keine Kennzahlen wie "Durchschnittliche Bearbeitungszeit" oder "Top-Filialen" beeinflussen.
- `status` und `customer.country` werden nicht normalisiert. Sie sind uneinheitlich (`"Closed"`/`"closed"`/`"Resolved"`, bzw. `"DE"`/`"de"`/`"Deutschland"`) aber auch nicht für die geforderten Queries notwendig und wurden deshalb ausgelassen um Zeit zu sparen.
- `comment`: Unverändert übernommen. Fehlt der Key vollständig im JSON, wird daraus automatisch `NULL` beim Laden in die Tabelle.
- Ein Datensatz pro `case_id`: Bei mehreren Versionen (unterscheidbar über `last_modified`) gewinnt der neuste Stand. Dabei deduplizieren wir in Pandas bevor wir in DuckDB schreiben, damit auch Mehrfachvorkommen innerhalb eines API-Batches sauber behandelt werden (Pagination überlappt sich um 5 Records pro Seite).

## Aus Zeitgründen nicht fertig geworden 
Die 3 Stunden haben für `queries.sql` und die `pytest`-Tests nicht mehr gereicht.

### Queries.sql
Query 1: `handling_minutes` pro Kategorie und Kalenderwoche

Wichtig hierbei: 
- Kalenderwoche sinnvoll definieren: über `closed_at`, da die Bearbeitungsdauer in direktem Bezug zum Abschlusszeitpunkt steht. 
- Nur geschlossene und nicht gelöschte Fälle einbeziehen 
- Negative `handling_minutes` rausfiltern um Durchschnitt nicht zu verfälschen

Query 2: die 10 Filialen (`store_no`) mit den meisten geschlossenen Cases, mit dem Anteil an allen Cases der Filiale

Wichtig hierbei: 
- Anteil an allen Cases der Filiale = geschlossene / (offene + geschlossene) Cases dieser Filiale 
- Gelöschte Cases nicht mit einbeziehen 

### Tests
Erst war ein Test für negative `handling_minutes` geplant. Später wurde allerdings bewusst entschieden, diese Werte unverändert mit aufzunehmen und später in den Queries zu berücksichtigen. 

1. `test_dedup_keep_latest`
- Selbe `case_id` mit unterschiedlichen `last_modified`
- Erwartet wird genau eine Zeile mit dem neusten Stand
2. `test_created_at_both_formats`
- Beide Datumsformate müssen auf denselben `TIMESTAMP` abbilden
3. `test_category_normalization`
- Alle Rohvarianten müssen auf genau 4 eindeutige Werte abbilden


## Fake Case API — Setup

## Installieren

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## API starten

```bash
python -m fake_api.server
```

Läuft auf `http://127.0.0.1:8080`. Zum Prüfen, ob sie lebt:

```bash
curl http://127.0.0.1:8080/health
```

## Zugangsdaten

```
client_id     = trainee-task
client_secret = s3cret-do-not-tell
```

Token holen:

```bash
curl -X POST http://127.0.0.1:8080/oauth/token \
  -H 'Content-Type: application/json' \
  -d '{"client_id":"trainee-task","client_secret":"s3cret-do-not-tell"}'
```

Daten abrufen:

```bash
curl -H "Authorization: Bearer <token>" \
  'http://127.0.0.1:8080/api/cases?closed_on=2026-07-14&offset=0&limit=100'
```

Die Daten sind synthetisch und bei jedem Start identisch. Der abgedeckte
Zeitraum ist Juni bis August 2026.

Die Aufgabenstellung steht in [AUFGABE.md](AUFGABE.md).

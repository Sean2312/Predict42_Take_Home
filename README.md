# Fake Case API — Setup

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

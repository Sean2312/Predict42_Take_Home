# Take-Home: Case-Daten von einer API in eine lokale Datenbank

Hallo Lennart,

diese Aufgabe ist eine vereinfachte, anonymisierte Version von etwas, das bei
uns wirklich läuft: Wir holen jeden Tag Daten aus APIs von Kunden und
Dienstleistern, bringen sie in eine auswertbare Form und laden sie in ein
Data Warehouse. Die APIs sind dabei nie so freundlich, wie die Doku behauptet.

**Zeitbudget: 3 Stunden.** Wir bewerten nicht, ob du fertig wirst, sondern wie
du arbeitest und was du bemerkst. Wenn dir die Zeit ausgeht: schreib in die
README, was du noch gemacht hättest und warum. Das zählt genauso viel wie Code.
Bitte kein Overengineering — keine Config-Frameworks, keine Abstraktionsebenen
"für später".

Alles läuft lokal. Du brauchst keinen Cloud-Zugang und kein Konto irgendwo.

## Das Szenario

Im Ordner `fake_api/` liegt eine kleine API, die einen Ticket-/Case-Datensatz
ausliefert (siehe `README.md` zum Starten). Sie hat drei Endpoints:

| Endpoint | Zweck |
| --- | --- |
| `POST /oauth/token` | Token holen (client_credentials) |
| `GET /api/cases?closed_on=YYYY-MM-DD` | alle Cases, die an diesem Tag geschlossen wurden |
| `GET /api/cases/updated?since=YYYY-MM-DD` | alle Case-Stände, die seit dem Datum geändert wurden |

Beide Listen-Endpoints sind paginiert (`offset`, `limit`) und brauchen
`Authorization: Bearer <token>`.

Ein Case ist ein JSON-Objekt und sieht ungefähr so aus:

```json
{
  "case_id": "CS-001721",
  "store_no": "00205",
  "created_at": "2026-08-22T06:30:00Z",
  "last_modified": "2026-08-22T11:50:00Z",
  "closed_at": "2026-08-22T11:50:00Z",
  "category": "Payment",
  "priority": "",
  "status": "Resolved",
  "handling_minutes": "-320",
  "customer": {"id": "C7607", "country": "at", "email": null},
  "comment": "n/a",
  "deleted": false
}
```

## Deine Aufgabe

Schreib eine Pipeline (`pipeline.py` oder ein kleines Package, dein Aufruf),
die per CLI startbar ist und die Cases aus der API in eine lokale
**DuckDB**-Datei `cases.duckdb` in eine Tabelle `cases` lädt.

Zwei Modi, wie bei uns in echt:

1. **Backfill** — für einen Tag oder einen Zeitraum, über `closed_on`
   ```
   python pipeline.py --date 2026-07-14
   python pipeline.py --date-from 2026-07-01 --date-to 2026-07-14
   ```
2. **Inkrementell** — der tägliche Lauf, über `updated`
   ```
   python pipeline.py --since 2026-08-25
   ```

### Anforderungen

1. **Wiederholbar.** Denselben Befehl zweimal laufen lassen darf die Tabelle
   nicht verdoppeln und nichts verlieren. Das ist die wichtigste Anforderung
   der ganzen Aufgabe.
2. **Vollständig.** Hol alle Seiten, nicht nur die erste.
3. **Robust.** Die API fällt gelegentlich um (`503`) und bremst dich
   (`429` mit `Retry-After`). Tokens laufen nach zwei Minuten ab. Ein Lauf
   soll das aushalten, ohne dass du ihn von Hand neu startest.
4. **Sauber typisiert.** In DuckDB sollen Datumsfelder Timestamps sein und
   Zahlen Zahlen — aber nur da, wo das inhaltlich stimmt. Schau dir die Daten
   vorher an; ein paar Felder sind nicht das, wonach sie aussehen.
5. **Ein Datensatz pro Case.** `case_id` ist der Schlüssel. Wenn ein Case
   mehrfach vorkommt, gewinnt der neueste Stand.
6. **Zwei SQL-Queries** in `queries.sql`, die auf der geladenen Tabelle laufen:
   - durchschnittliche Bearbeitungsdauer pro Kategorie und Kalenderwoche
   - die 10 Filialen (`store_no`) mit den meisten geschlossenen Cases,
     mit dem Anteil an allen Cases der Filiale
7. **2–4 Tests** mit `pytest`. Wichtig: Die Tests dürfen **die API nicht
   aufrufen** — kein Netzwerk, kein laufender Server. Teste deine
   Transformationslogik mit Beispieldaten, die du im Test selbst baust.
8. **README** mit: wie man es startet, welche Annahmen du getroffen hast,
   was dir an den Daten aufgefallen ist, und was du weggelassen hast.

### Was wir ausdrücklich nicht erwarten

Kein Docker, kein CI, keine Cloud, kein Logging-Framework, keine 100 %
Testabdeckung, keine Performance-Optimierung. Pandas oder Polars — nimm, was
du kennst.

## Abgabe

Ein Git-Repo (Zip oder Link) mit deinem Code, `queries.sql`, den Tests und der
README. Commit-Historie gern in kleinen Schritten, wir schauen sie uns an.

Im Technical Interview reden wir ~25 Minuten über deinen Code: du zeigst ihn,
wir fragen nach. Wenn du an einer Stelle bewusst eine Abkürzung genommen hast,
sag es einfach — dokumentierte Abkürzungen sind für uns ein gutes Zeichen.

Bei Fragen zur Aufgabe schreib mir gern direkt, das ist kein Punktabzug.

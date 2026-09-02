## Plan
### 0: Daten Explorieren
- API starten und ein paar echte Antworten mit `curl` anschauen
- Daten begutachten, festhalten was auffällig ist 
- Pagination und Fehlerfelle anschauen 
- Fertig, wenn: eine Antwort mit Pagination gesehen und Fehlercodes (503/429) aufgetreten sind 

### 1: Minimale Pipeline 
- Auth Token holen 
- Ersten `GET`-Request machen
- Rows unverändert in DuckDB schreiben 
- Argparser für `--date yyyy-mm-dd` schreiben
- Fertig, wenn: `python pipeline.py --date yyyy-mm-dd` durchläuft und `cases.duckdb` Daten enthält

### 2: Pagination
- Alle Seiten für einen Tag holen
- Abbruch wenn leere items-Liste
- Fertig, wenn: mehr als eine Seite geladen und Anzahl der Cases mit manueller Kontrolle übereinstimmt 

### 3: Robust 
- 1. 429 abfangen und `Retry-After` beachten 
- 2. 503 (Backoff) -> erneut versuchen 
- 3. 401 token expired -> neu authentifizieren 
- Fertig, wenn: mehrere hundert Requests ohne manuelles Eingreifen durchlaufen (auch wenn Lauf viel Zeit benötigt)

### 4: Deduplikation (WICHTIG!)
- Doppelt vorkommende Cases über `case_id` identifizieren
- Neuster Stand gewinnt (`last_modified`)
- Bereinigte Daten in DuckDB speichern 
- Fertig, wenn: derselbe Befehl zweimal hintereinander ausgeführt werden kann und die Tabelle identisch ist

### 5: Typisierung
- Datumsfelder als `TIMESTAMP` speichern 
- Zahlen zu `INTEGER` machen (wenn sinnvoll)
- Daten bereinigen 
- Fertig, wenn: mithilfe von `DESCRIBE` sinnvolle Typen angezeigt werden und die Daten plausibel aussehen 

### 6: --since und Datumsbereich
- `api/cases/updated` anbinden
- `--date-from` und `--date-to` ergänzen
- Bei einem Datumsbereich die einzelnen Tage abarbeiten
- Möglichst über selbe Lade- und Dedup-Funktonalität
- Fertig, wenn Tagesabfrage und Datumsbereich funktionieren

### 7: Queries
- 1. Durchschnittliche Bearbeitungsdauer pro Kategorie und Kalenderwoche (`handling_minutes`, `category`, Kalenderwoche)
- 2. Die 10 Filialen mit den meisten geschlossenen Cases, mit dem Anteil an allen Cases der Filiale (`store_no`)
- Fertig, wenn: beide Queries in DuckDB laufen und Ergebnisse plausibel aussehen

### 8: Tests 
- 2-4 `pytest`-Tests für Transformationslogik schreiben (synthetische Daten, kein Server Zugriff)
- Dedup und neuster gewinnt
- `handling_minutes` 
- ...
- Fertig, wenn: `pytest` grün ist 

### 9: README
- Startanleitung 
- Wichtige Annahmen/Entscheidungen dokumentieren
- Was ist an den Daten aufgefallen, welche Unstimmigkeiten sind aufgetreten
- Dinge, die aus Zeitgründen weggelassen wurden

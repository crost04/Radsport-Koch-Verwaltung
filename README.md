# Radsport Koch – Verwaltung

Warenwirtschaft für einen Fahrradhändler: Kunden, Artikel und Bestellungen in einer Desktop-Anwendung mit relationaler Datenbank – inklusive Umsatzauswertung mit Mehrwertsteuer.

Projektarbeit im Fach Datenbanken meiner Weiterbildung zum staatlich geprüften KI-Techniker.

## Funktionsumfang

Die Anwendung ist in drei Reiter gegliedert:

**Kunden** – anlegen, bearbeiten, suchen, löschen.

**Artikel** – Bezeichnung und Preis verwalten, Preisformatierung in Euro.

**Bestellungen & Umsatz** – Bestellungen aus Kunde, Artikel und Menge zusammensetzen, Gesamtpreis je Position, laufende Umsatzauswertung.

Über alle Bereiche hinweg gibt es eine **Live-Suche**, die schon beim Tippen filtert, einen **Papierkorb statt endgültigem Löschen** – gelöschte Einträge sind zunächst nur ausgeblendet und lassen sich wiederherstellen, erst ein zweiter, deutlich gekennzeichneter Schritt entfernt sie wirklich – und eine **Umsatzauswertung** in Brutto, enthaltener 19 % Mehrwertsteuer und Netto, in deutscher Zahlenschreibweise.

## Datenmodell

Drei Tabellen in SQLite, über Fremdschlüssel verbunden:

```
kunden        id · name · email · aktiv
artikel       id · bezeichnung · preis · aktiv
bestellungen  id · kunde_id → kunden.id · artikel_id → artikel.id · menge · aktiv
```

Die Bestellliste entsteht über einen JOIN über alle drei Tabellen – so stehen in der Oberfläche Namen statt IDs, und der Zeilenpreis wird direkt in der Abfrage berechnet:

```sql
SELECT b.id, k.name, a.bezeichnung, b.menge, (b.menge * a.preis)
FROM bestellungen b
JOIN kunden  k ON b.kunde_id  = k.id
JOIN artikel a ON b.artikel_id = a.id
WHERE b.aktiv = ?
```

## Drei Entscheidungen, die mir wichtig waren

**Soft Delete statt DELETE.** Jede Tabelle hat eine Spalte `aktiv`. Löschen setzt sie auf 0, der Datensatz verschwindet nur aus der Ansicht. In einem Betrieb ist ein versehentlich gelöschter Kunde teurer als eine Zeile zu viel in der Datenbank.

**Fremdschlüssel wirklich erzwingen.** SQLite prüft Fremdschlüssel standardmäßig nicht – `PRAGMA foreign_keys = ON` wird bei jeder Verbindung gesetzt. Damit kann keine Bestellung ohne zugehörigen Kunden existieren. Beim endgültigen Löschen werden abhängige Bestellungen deshalb bewusst zuerst entfernt.

**Parametrisierte Abfragen.** Alle Werte gehen als Parameter in die SQL-Anweisung, nie über String-Verkettung. Das schließt SQL-Injection aus – auch wenn hier nur ein einzelner Anwender tippt, ist alles andere eine schlechte Angewohnheit.

## Technik

| Bereich | Eingesetzt |
|---|---|
| Sprache | Python |
| Oberfläche | PySide6 (Qt), gestaltet über ein Qt-Stylesheet |
| Datenhaltung | SQLite, ohne Serverinstallation |
| Fehlerbehandlung | zentrale Abfragefunktion mit `try`/`except` und Dialogmeldung bei Datenbankfehlern |

## Starten

```bash
pip install PySide6
python radsport_verwaltung.py
```

Die Datenbankdatei `radsport_koch.db` wird beim ersten Start automatisch angelegt.

---

*Christian Rost · Weiterbildung zum staatlich geprüften KI-Techniker*

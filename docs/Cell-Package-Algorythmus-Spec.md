Hier ist eine detaillierte und technisch präzise Spezifikation, die du an einen KI-Coder oder Softwareentwickler weitergeben kannst.

Zuvor jedoch eine **wichtige technische Korrektur/Präzisierung** zu deiner Anforderung bezüglich des Innenwiderstands ($$R_i$$), die ich in die Spezifikation eingearbeitet habe:

> **Korrektur:** Das Ziel sollte nicht nur sein, Zellen mit "minimalem $$R_i$$" in eine Gruppe zu packen (denn du hast ja nur die Zellen, die du hast), sondern den **Gesamtwiderstand der parallelen Gruppen anzugleichen**.
>
> *Warum?* Wenn Gruppe 1 einen Gesamtwiderstand von $$10 m\\Omega$$ hat und Gruppe 2 hat $$15 m\\Omega$$, wird Gruppe 1 unter Last weniger Spannung verlieren als Gruppe 2. Das BMS misst unterschiedliche Spannungen und schaltet früher ab. Zudem wird Gruppe 2 wärmer.
> **Ziel:** Alle P-Gruppen sollen den gleichen mittleren $$R_i$$ haben, damit sich der "Voltage Sag" (Spannungseinbruch) und die Wärmeentwicklung gleichmäßig verteilen.

Hier ist der Prompt / die Spezifikation für den Coder:

---

# Spezifikation: Advanced Battery Pack Builder Algorithm

## 1. Projektziel

Erweiterung eines bestehenden Algorithmus zur Zusammenstellung von Akkupacks (Li-Ion Zellen). Der Algorithmus soll Zellen aus einem verfügbaren Inventar so auf parallele Gruppen (P-Gruppen) verteilen, dass sowohl die **Kapazität** als auch der **Innenwiderstand ($$R_i$$)** über alle Serien-Gruppen hinweg perfekt balanciert sind. Zusätzlich wird eine "Hot-Swap"-Funktion für defekte Zellen benötigt.

## 2. Datenstrukturen & Input

Verwende in jedem Fall die bestehende Datenbankfeldnamen  und Variablen, welche bereits im aktuellen Algorythmus existieren! 

**Input Parameter:**

* `cells_inventory`: Liste aller verfügbaren Zellen (Objekte).
* `config_s`: Anzahl der Serien-Gruppen (z.B. 10).
* `config_p`: Anzahl der Zellen parallel pro Gruppe (z.B. 4).
* `filter_min_cap`: Minimale Kapazität (mAh) für Berücksichtigung.
* `filter_max_cap`: Maximale Kapazität (mAh) für Berücksichtigung.

**Zell-Objekt Struktur:**

* `id`: Eindeutige ID (String/Int).
* `capacity`: Gemessene Kapazität in mAh (Float).
* `resistance`: Gemessener AC Innenwiderstand in $$m\\Omega$$ (Float).
* `status`: 'available', 'assigned', 'defective'.

## 3. Algorithmus-Logik (Kernanforderung)

Der Algorithmus muss in zwei Phasen arbeiten: **Filterung** und **Optimierung**.

---

# Spezifikation: Phase A - Auswahlstrategie (Nachhaltiges Bestandsmanagement)

## Kontext

Der Benutzer verwaltet ein großes Inventar (~20.000 Zellen). Das Ziel ist es NICHT, das Akkupack mit der absolut höchsten Kapazität zu bauen (indem nur die besten Zellen gepickt werden), sondern ein Pack zu bauen, das die **durchschnittliche Qualität** des aktuell verfügbaren Inventars im gewählten Bereich widerspiegelt. Dies stellt sicher, dass für zukünftige Projekte keine reine "Resterampe" (nur schlechte Zellen) übrig bleibt.

## Phase A: Filterung & Selektionslogik

### 1. Bereichsfilterung (Positive Selektion)

Selektiere alle Zellen aus dem `cells_inventory`, die die Kriterien des Benutzers erfüllen:

* `Zelle.kapazität >= filter_min_cap`
* UND `Zelle.kapazität <= filter_max_cap`
* UND `Zelle.status == 'verfügbar'`

Nennen wir diese Liste `gueltige_kandidaten`.

### 2. Repräsentatives Sampling (Die "Äquidistante" Methode)

Wir müssen exakt `N` Zellen (`N = config_s * config_p`) aus den `gueltige_kandidaten` auswählen.

**Algorithmus:**

1. **Sortieren:** Sortiere `gueltige_kandidaten` primär nach `kapazität` (aufsteigend) und sekundär nach `innenwiderstand` (absteigend). 
   * *Das Sortieren erzeugt einen Gradienten von "schlechteste" zu "beste" Zelle innerhalb des gültigen Bereichs.*
2. **Schrittweite berechnen:** 
   * `step = anzahl(gueltige_kandidaten) / N`
3. **Zellen auswählen:** 
   * Iteriere `i` von `0` bis `N-1`.
   * Wähle die Zelle am Index `abrunden(i * step)`.
   * Markiere diese ausgewählten Zellen als `fuer_pack_gewaehlt`.
   * Alle nicht gewählten Zellen verbleiben im `reserve_pool` (wichtig für die spätere "Defekte Zelle ersetzen"-Logik).

**Beispiel-Logik:**
Wenn wir 1000 gültige Kandidaten haben und 100 Zellen benötigen:

* Wir nehmen Index 0, 10, 20, 30...
* Auf diese Weise enthält das ausgewählte Pack eine Mischung aus Zellen mit niedrigerer, mittlerer und höherer Kapazität, was die Verteilung des gesamten Inventars perfekt widerspiegelt.

### 3. Ausreißer-Check (Sicherheit)

* Auch wenn wir einen Durchschnittsmix wollen, darf keine Zelle mit einem gefährlich hohen Innenwiderstand ($$R_i$$) ausgewählt werden.
* Füge einen Parameter `max_erlaubter_widerstand` hinzu. Falls eine durch das Sampling gewählte Zelle diesen Wert überschreitet, verwerfe sie und nimm den direkten Nachbarn aus der sortierten Liste, der diesen Wert einhält.

---

### Phase B: Multi-Objective Balancing (Verteilung)

Das Ziel ist die Minimierung der Standardabweichung (Deviation) zwischen den P-Gruppen für zwei Metriken gleichzeitig.

**Metrik 1: Gruppen-Kapazität ($$C\_{group}$$)**

* $$C\_{group} = \\sum (Cell\_{capacity})$$
* **Ziel:** $$C\_{group_1} \\approx C\_{group_2} \\approx \\dots \\approx C\_{group_n}$$

**Metrik 2: Gruppen-Widerstand ($$R\_{group}$$)**

* *Physikalischer Hinweis:* Bei Parallelschaltung addieren sich die Leitwerte.
* $$R\_{group} = 1 / \\sum (1 / Cell\_{resistance})$$
* **Ziel:** $$R\_{group_1} \\approx R\_{group_2} \\approx \\dots \\approx R\_{group_n}$$

**Implementierungs-Strategie (Vorschlag für den Coder):**
Verwende einen **Iterativen Tausch-Algorithmus (Repacker)**:

1. **Initialverteilung:** Sortiere Zellen nach Kapazität und verteile sie schlangenförmig (Serpentine) auf die Gruppen, um eine grobe Kapazitätsbalance zu erreichen.
2. **Optimierungsschleife:** 
   * Berechne die durchschnittliche Kapazität und den durchschnittlichen Widerstand aller Gruppen.
   * Identifiziere die Gruppe mit der stärksten Abweichung (z.B. höchste Kapazität oder niedrigster Widerstand).
   * Suche in einer anderen Gruppe eine Zelle zum Tauschen.
   * **Tausch-Bedingung:** Ein Tausch wird nur durchgeführt, wenn er den **Globalen Score** verbessert.
   * **Score-Funktion:** $$Score = (w_1 \\cdot \\text{StdDev}*{Cap}) + (w_2 \\cdot \\text{StdDev}*{Res})$$. 
     * Empfehlung Gewichtung: Kapazität ist kritischer für die Balance beim Laden/Entladen, Widerstand für die Wärme. Priorisiere Kapazität leicht ($$w_1=0.6, w_2=0.4$$).

## 4. Feature: Defective Cell Replacement (Ersatzteil-Finder)

Es soll eine Funktion `find_replacement_cell(group_id, defective_cell_id, reserve_pool)` implementiert werden.

**Szenario:**
Der Pack ist fertig berechnet. Beim physischen Bau fällt eine Zelle auf den Boden oder lässt sich nicht löten. Sie wird als "defekt" markiert.

**Logik:**

1. Entferne die `defective_cell` aus der `group_id`.
2. Durchsuche den `reserve_pool` (nicht genutzte Zellen).
3. Finde die "Beste Übereinstimmung" (Best Match).
4. **Kriterien für Best Match:** 
   * Die neue Zelle muss die Kapazität der Gruppe so wiederherstellen, dass die Abweichung zum ursprünglichen Gruppen-Wert minimal ist.
   * Delta Kapazität: $$| Cell\_{new}.Cap - Cell\_{old}.Cap |$$ -> minimieren.
   * Delta Widerstand: $$| Cell\_{new}.Res - Cell\_{old}.Res |$$ -> minimieren.
5. Gebe die ID der besten Ersatzzelle zurück und aktualisiere die Gruppen-Statistik.

## 5. Output Format

Das Ergebnis soll ein JSON-Objekt sein:

```json
{
  "pack_summary": {
    "avg_group_capacity": 10000.0,
    "capacity_deviation_percent": 0.05,
    "avg_group_resistance": 12.5,
    "resistance_deviation_percent": 1.2
  },
  "groups": [
    {
      "group_id": 1,
      "total_capacity": 10005,
      "total_resistance_ohm": 0.012,
      "cells": [ { "id": "A1", "cap": 2500, "res": 45 }, ... ]
    },
    ...
  ],
  "reserve_pool": [ ... ]
}
```

---

### Hinweise für dich zur Nutzung:

* **Algorithmus-Wahl:** Ein einfacher Sortieralgorithmus reicht hier oft nicht. Der Coder sollte idealerweise einen **"Simulated Annealing"** oder **"Genetic Algorithm"** Ansatz wählen, oder zumindest einen **"Greedy Swap"** Algorithmus, der so lange Zellen tauscht, bis keine Verbesserung mehr möglich ist.
* **Rechenzeit:** Bei sehr vielen Zellen (z.B. >500) kann die Berechnung ein paar Sekunden dauern. Das ist normal.
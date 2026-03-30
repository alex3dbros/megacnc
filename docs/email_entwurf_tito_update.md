# E-Mail-Entwurf an Tito (Update App)

**Betreff:** Bitte heute Abend zuerst App-Update – Stand MegaCNC (User-Sicht)

---

Hallo Tito,

bitte **heute Abend zuerst ein Update der App** einplanen (Pull/Build/Deploy wie bei euch üblich), damit die aktuelle Version mit den Verbesserungen unten läuft.

Kurz aus **Nutzersicht**, was sich gebessert hat bzw. neu ist:

- **Handbuch:** Benutzerhandbuch direkt in der App (Anzeige + PDF-Export), statt nur lose Datei  
- **Docker:** Image baut deutlich **schneller** und zuverlässiger (kein unnötig riesiger Build-Kontext mehr); `requirements.txt` technisch bereinigt (u. a. PDF-Druck)  
- **Drucken / QZ Tray:** Signierung läuft **über den Server** – weniger Probleme mit „Untrusted“/Allow-Dialogen; Anleitung für das **Demo-Zertifikat** liegt in der Doku  
- **Einstellungen:** Beim Wechsel der **Tabs** scrollt die Seite nicht mehr unwillkürlich nach oben  
- **Database:** Status **Available / Not Available** ist **farbig** erkennbar (grün/rot)  
- **Database:** **Drucken** von der Seite funktioniert wieder wie erwartet  
- **Batterie-Packs (Balancing):** bei **großen Packs** spürbar **flüssiger** (Hintergrund-Berechnung, weniger Ruckeln)  
- **Version** der App: **1.1.0**  
- **Wartung:** Update-/Deploy-Abläufe und Skripte sind etwas **robuster** (z. B. docker-compose nach Pull, Aufräumen alter Images beim Deploy)

Wenn du Fragen zum Rollout hast, melde dich.

Viele Grüße  
[Name]

---

*Basierend auf den letzten Git-Commits bis einschließlich `1de570a`.*

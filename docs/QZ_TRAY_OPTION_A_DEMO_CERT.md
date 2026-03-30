# QZ Tray Option A: Demo-Zertifikat (einheitlich mit Site Manager)

Die App nutzt `certificate/qz-tray-public.pem` und `certificate/qz-tray-private.pem`.  
Diese **müssen** zum Zertifikat passen, das in **QZ Tray → Site Manager** als erlaubt steht (z. B. „QZ Tray Demo Cert“).

## Schritt 1: Demo-Zertifikat erzeugen (falls noch kein Ordner auf dem Desktop)

1. **QZ Tray** starten (Tray-Icon).
2. Rechtsklick auf Icon → **Advanced** → **Site Manager**.
3. Unten **+** klicken → **Create New** / Zertifikat anlegen.
4. Mit **Yes** bestätigen, bis QZ die Dateien erzeugt.
5. Es erscheint ein Ordner **„QZ Tray Demo Cert“** (meist auf dem **Desktop**).

> Wenn der Ordner schon existiert (z. B. früher angelegt), Schritt 1 überspringen.
for d in "$HOME/Desktop" "$HOME/Schreibtisch" "$HOME"; do [ -d "$d" ] && ls -la "$d" 2>/dev/null | head -5; done; echo "---"; find "$HOME" -maxdepth 3 \( -iname '*QZ*Demo*' -o -iname '*Demo*Cert*' \) -type d 2>/dev/null; echo "---"; find "$HOME" -maxdepth 5 -name 'digital-certificate.txt' 2>/dev/null; find "$HOME" -maxdepth 5 -path '*QZ*' -name 'private-key.pem' 2>/dev/null | head -15

## Schritt 2: Dateien im Ordner finden

Im Ordner **„QZ Tray Demo Cert“** gibt es typischerweise:

| Datei (Beispiel)        | Bedeutung        |
|-------------------------|------------------|
| `digital-certificate.txt` | Öffentliches Zertifikat (PEM-Text) |
| `private-key.pem`       | Private Key (geheim)               |

Namen können minimal abweichen; wichtig ist: **ein** öffentliches Zertifikat + **ein** Private Key im PEM-Format.

## Schritt 3: In das Projekt kopieren (MegaCNC-Repo)

**Zielpfade (immer gleich):**

- Öffentlich: `certificate/qz-tray-public.pem`
- Privat:   `certificate/qz-tray-private.pem`

### Linux / macOS (Terminal, Pfade anpassen)

```bash
cd /PFAD/ZU/megacnc

# Desktop-Pfad anpassen, z. B.:
# DEMO="$HOME/Desktop/QZ Tray Demo Cert"
DEMO="$HOME/Desktop/QZ Tray Demo Cert"

cp "$DEMO/digital-certificate.txt" certificate/qz-tray-public.pem
cp "$DEMO/private-key.pem" certificate/qz-tray-private.pem
chmod 600 certificate/qz-tray-private.pem

oder
cd /home/heinz/megacnc
cp "/home/heinz/Downloads/QZ Tray Demo Cert/digital-certificate.txt" certificate/qz-tray-public.pem
cp "/home/heinz/Downloads/QZ Tray Demo Cert/private-key.pem" certificate/qz-tray-private.pem
chmod 600 certificate/qz-tray-private.pem
```

Wenn die Datei `digital-certificate.txt` anders heißt, den ersten `cp`-Quellnamen anpassen.

### Windows (Explorer)

1. Ordner **„QZ Tray Demo Cert“** auf dem Desktop öffnen.
2. Datei **digital-certificate.txt** → Inhalt oder Datei nach  
   `megacnc\certificate\qz-tray-public.pem` kopieren (bestehende Datei **ersetzen**).
3. Datei **private-key.pem** → nach  
   `megacnc\certificate\qz-tray-private.pem` kopieren (**ersetzen**).

## Schritt 4: Docker-Image neu bauen und starten

Im Projektroot:

```bash
docker compose build --no-cache web
docker compose up -d
```

## Schritt 5: Prüfen

1. Browser: `http://localhost:8000/qz/certificate/`  
   → Muss mit `-----BEGIN CERTIFICATE-----` beginnen.
2. Seite mit Druck/QZ hart neu laden (Strg+F5).
3. In QZ Tray sollte dieselbe Identität erscheinen wie unter **Site Manager → Allowed** (Demo Cert).

## Schritt 6: Erneut erlauben (einmal)

Beim ersten Zugriff ggf. **Allow** klicken; **Remember this decision** erst testen, wenn **Allow** ohne Grau-Button funktioniert.

## Probleme

- **Allow grau bei „Remember“:** Zuerst nur **Allow** ohne Häkchen; oder Zertifikat/Key prüfen (Schritt 3 wirklich ersetzt?).
- **Alter Eintrag in Site Manager:** Nach Dateiwechsel QZ Tray **neu starten** und Seite neu laden.

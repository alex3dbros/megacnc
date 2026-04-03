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

### Windows (Kundensystem) – gleicher Ablauf wie unter Linux

**Schritt 1–2:** Wie oben: QZ Tray → **Site Manager** → Zertifikat anlegen. Der Ordner **„QZ Tray Demo Cert“** liegt typischerweise auf dem **Desktop**, z. B.:

`C:\Users\<Benutzername>\Desktop\QZ Tray Demo Cert\`

(Bei deutscher Windows-Oberfläche heißt der Desktop-Ordner oft **Desktop**; der QZ-Ordnername bleibt meist **QZ Tray Demo Cert**.)

**Schritt 3 – Varianten:**

**A) Explorer**

1. Ordner **„QZ Tray Demo Cert“** öffnen.
2. **digital-certificate.txt** → nach `<Pfad-zum-Repo>\certificate\qz-tray-public.pem` kopieren (**ersetzen**).
3. **private-key.pem** → nach `<Pfad-zum-Repo>\certificate\qz-tray-private.pem` kopieren (**ersetzen**).

**B) PowerShell** (Pfade anpassen: Repo + ggf. anderer Demo-Ordner, z. B. Downloads):

```powershell
$Repo = "C:\Pfad\zu\megacnc"
$Demo = "$env:USERPROFILE\Desktop\QZ Tray Demo Cert"

Copy-Item -LiteralPath "$Demo\digital-certificate.txt" -Destination "$Repo\certificate\qz-tray-public.pem" -Force
Copy-Item -LiteralPath "$Demo\private-key.pem" -Destination "$Repo\certificate\qz-tray-private.pem" -Force
```

> Unter Windows entfällt `chmod`; optional nur für restriktive Rechte auf dem Private Key:  
> `icacls "$Repo\certificate\qz-tray-private.pem" /inheritance:r /grant:r "$env:USERNAME:(R)"`

## Schritt 4: Docker-Image neu bauen und starten

Im Projektroot (Linux/macOS: Terminal; **Windows:** PowerShell oder CMD im Repo-Ordner, **Docker Desktop** muss laufen):

```bash
docker compose build --no-cache web
docker compose up -d
```

## Schritt 5: Prüfen

1. Browser: `http://localhost:8000/qz/certificate/`  
   → Muss mit `-----BEGIN CERTIFICATE-----` beginnen.
2. Seite mit Druck/QZ hart neu laden (Strg+F5).
3. In QZ Tray sollte dieselbe Identität erscheinen wie unter **Site Manager → Allowed** (Demo Cert).

## Schritt 6: Allow-Dialog – einmal erlauben, dann Ruhe

Mit **korrekter Signatur** (Zertifikat + Private Key im Server, passend zur Demo-Cert in QZ) zeigt QZ beim ersten Connect oft einen Dialog. Ziel:

1. **Allow** klicken.
2. Wenn möglich **Remember this decision** aktivieren (wenn der Button **nicht** grau ist). Dann sollte der Dialog **nicht bei jedem** weiteren Öffnen der Seite wiederkommen.

Ist **Remember** grau, zuerst nur **Allow** ohne Häkchen; Ursache ist meist eine **fehlgeschlagene Signatur** (siehe unten).

### Der Allow-Dialog soll nicht mehr kommen – kommt aber noch (jedes Mal)

Dann ist die Verbindung für QZ **nicht dauerhaft „trusted“**. Typische Ursachen:

| Ursache | Was tun |
|--------|---------|
| **Signatur schlägt fehl** (503/500 auf `/qz/sign/` oder Zertifikat 503) | Browser **F12 → Netzwerk**: Beim Connect müssen `/qz/certificate/` und `/qz/sign/` **200** liefern. Sonst PEM/Key im Container prüfen, Web-Container neu bauen. |
| **localhost vs. 127.0.0.1** gemischt | Nur **eine** URL nutzen (z. B. immer `http://localhost:8000`). Jede andere Origin braucht eine neue Freigabe. |
| **Freigabe nie gespeichert** | Einmal **Allow** + **Remember** (wenn nicht grau). |
| **Alter/zweiter Eintrag in Site Manager** | **Site Manager** öffnen: falsche oder doppelte Einträge entfernen, QZ **neu starten**, Seite **Strg+F5**. |
| **Demo-Zertifikat beim Anlegen nicht ins System übernommen** | Beim Erzeugen der Demo-Cert in QZ die Meldungen mit **Yes** bestätigen (u. a. Installation / **override.crt**), damit QZ dem Zertifikat vertraut – siehe [QZ Signing](https://github.com/qzind/tray/wiki/Signing). |
| **Komplett ohne Dialoge (auch kein erstes Mal)** | Nur mit **QZ-kommerziellem** Zertifikat von QZ Industries üblich; Demo/self-signed arbeitet fast immer mit mindestens einmaliger Bestätigung. |

### Kurz-Checkliste (Windows/Linux)

1. **Gleiche URL** immer (inkl. Port).
2. **Netzwerk-Tab:** `/qz/certificate/` und `/qz/sign/` → **200**.
3. **Site Manager:** passende Origin unter **Allowed**; QZ nach Änderungen neu starten.
4. **Firewall:** localhost / QZ-Ports (u. a. **8181**, **8182**) nicht blockieren.

## Probleme

- **Allow grau bei „Remember“:** Signatur prüfen (Netzwerk-Tab); Zertifikat/Key im Repo; Schritt 4 (Docker) nicht vergessen.
- **Alter Eintrag in Site Manager:** QZ Tray **neu starten**, Seite neu laden.
- **Allow jedes Mal:** Oben Abschnitt „soll nicht mehr kommen“.

# Taxi Akbulut – Social-Autopilot

Postet automatisch Werbebilder auf Instagram (Feed + Story) und Facebook (ausgewählte Themen auch auf der LinkedIn-Unternehmensseite), 5× pro Woche nach Themen-Tagen (Mo Taxi Tübingen, Di Krankenfahrten, Mi Flughafen, Do Ferntaxi, Fr Event-Shuttle/Medizinkurier im Wechsel, jeweils 18:00), plus 1 Reel mit eigener Musik pro Woche (Sa 11:00).
Kostenlos: GitHub Actions veröffentlicht, Claude füllt jede Woche die Warteschlange mit neuen Bildern.

```
queue/        geplante Posts (JSON: Datum, Bild, Text)
reels/        Reels (MP4, werden direkt zu Instagram hochgeladen)
stories/      Story-Versionen der Bilder (9:16)
images/       Bilder (JPEG, öffentlich über GitHub abrufbar – Instagram verlangt das)
published/    veröffentlichte Posts mit Instagram-/Facebook-ID
failed/       Posts, die 3× fehlgeschlagen sind
redaktion/    Fakten und Regeln – die einzige Quelle für Inhalte
vorlagen/     Gestaltungsvorlagen aller bisherigen Motive
generator/    Renderer für neue Motive (HTML → JPEG)
publisher/    Veröffentlichungs-Skript für GitHub Actions
```

## Einmalige Einrichtung (ca. 30 Minuten)

### 1. Instagram vorbereiten
- Instagram-Konto muss ein **Business- oder Creator-Konto** sein
  (Instagram → Einstellungen → Kontotyp und Tools).
- Es muss mit der **Facebook-Seite** von Taxi Akbulut verknüpft sein
  (Meta Business Suite → Einstellungen → Konten → Instagram-Konten).

### 2. Zugangsschlüssel bei Meta erzeugen (Systemnutzer – läuft nicht ab)
1. business.facebook.com → **Business-Einstellungen** → Nutzer → **Systemnutzer**.
   (Für WhatsApp gibt es vermutlich schon einen – den kannst du nehmen.)
2. Dem Systemnutzer unter „Assets zuweisen" die **Facebook-Seite** und das **Instagram-Konto** zuweisen (volle Kontrolle).
3. Unter Business-Einstellungen → **Apps**: deine Meta-App (z. B. die WhatsApp-App) dem Systemnutzer zuweisen.
   In der App (developers.facebook.com) das Produkt **Instagram** bzw. „Instagram Graph API" hinzufügen.
4. Beim Systemnutzer **Token generieren** → App wählen → Ablauf **„Nie"** → diese Berechtigungen anhaken:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `business_management`.
   Den Token sicher kopieren → das ist **META_ACCESS_TOKEN**.
5. IDs ermitteln im **Graph API Explorer** (developers.facebook.com/tools/explorer) mit diesem Token:
   - `GET me/accounts` → `id` der Seite = **FB_PAGE_ID**
   - `GET <FB_PAGE_ID>?fields=instagram_business_account` → `id` = **IG_USER_ID**

> Den Token niemals per E-Mail, WhatsApp oder in diesen Chat schicken. Er gehört nur in die GitHub-Secrets.

### 3. GitHub einrichten
1. Kostenloses Konto auf github.com (falls nicht vorhanden).
2. Neues Repository **`taxi-akbulut-social`**, Sichtbarkeit **Public**
   (nur so sind die Bilder für Instagram öffentlich erreichbar; enthalten sind nur Werbebilder und Texte, keine Zugangsdaten).
3. Das Repository darf leer bleiben – Claude lädt den Inhalt nach Schritt 4 selbst hoch.
   (Alternativ selbst hochladen: „Add file → Upload files"; der Ordner `.github` muss mit.)
4. Repository → **Settings → Secrets and variables → Actions → New repository secret**, drei Secrets anlegen:
   `META_ACCESS_TOKEN`, `IG_USER_ID`, `FB_PAGE_ID`.
5. Repository → **Actions** → Workflows aktivieren, falls gefragt.
6. Test: Actions → „Social-Autopilot" → **Run workflow** (dry_run angehakt). Grüner Haken = alles bereit.

### 4. Claude verbinden
In Claude: GitHub-Konto verbinden und Claude Zugriff auf `taxi-akbulut-social` geben.
Dann im Chat Bescheid sagen – Claude legt den wöchentlichen Auftrag an.

## Wie es danach läuft
- **Alle 30 Minuten** prüft GitHub, ob ein Post fällig ist, und veröffentlicht ihn (höchstens einer pro Tag).
- **Jeden Sonntag** erstellt Claude neue Motive mit Texten nach `redaktion/` und plant sie ein.
  Du bekommst eine Zusammenfassung mit den Motiven der nächsten Woche.
- **Einen Post stoppen:** die Datei in `queue/` löschen (auf GitHub: Datei öffnen → Papierkorb-Symbol) oder Claude Bescheid sagen.
- **Fehler:** GitHub schickt dir automatisch eine E-Mail, wenn ein Lauf fehlschlägt.
- Die erste Planung startet am **Sonntag, 11.10.2026, 9:00 Uhr**, ab 12.10. Mo–Fr 18:00 nach Themen-Tagen und Sa 11:00 (Reel). Liegt die Einrichtung später, werden überfällige Posts
  einzeln nachgeholt – einer pro Tag.

## LinkedIn-Unternehmensseite (optional, kostenlos)

Solange die LinkedIn-Secrets fehlen, wird LinkedIn einfach übersprungen.

**Was gepostet wird:** Chauffeurservice, Ferntaxi, Flughafen, Medizinkurier, Event-Shuttle und Reels.
Pro Post änderbar mit `"linkedin": true` oder `false`. Eigener LinkedIn-Text optional mit `"linkedin_caption"`;
sonst wird der Instagram-Text angepasst (klickbarer Link statt „Link im Profil“, höchstens 3 Hashtags).

### 1. App anlegen und Zugang beantragen
1. Als Admin der LinkedIn-Seite von Taxi Akbulut auf **developers.linkedin.com** → **Create app**.
   - App-Name z. B. „Taxi Akbulut Autopilot“, als **LinkedIn Page** die Taxi-Akbulut-Seite wählen, Logo hochladen.
2. Im Reiter **Settings** → „Verify“ klicken und den Link als Seiten-Admin bestätigen.
3. Im Reiter **Products** → **Community Management API** → „Request access“.
   Formular ehrlich ausfüllen: *„Eigene Unternehmensseite: automatisches Veröffentlichen unserer eigenen Werbebeiträge
   (Bilder und Videos) eines Taxi- und Chauffeurunternehmens. Kein Zugriff auf fremde Seiten oder Mitgliederdaten.“*
   Firmenangaben (Adresse, Website, ggf. Handelsregister) bereithalten.
   - Wichtig: Die App darf **keine anderen Produkte** haben (z. B. nicht „Sign In with LinkedIn“), sonst lehnt LinkedIn ab.
   - Die Prüfung dauert meist einige Tage bis Wochen. Die Antwort kommt per E-Mail.

### 2. Zugangsschlüssel erzeugen (nach der Freigabe)
1. Im Reiter **Auth**: **Client ID** und **Primary Client Secret** kopieren.
2. Unter **Auth** → „OAuth 2.0 tools“ → **Create token** → Berechtigung **`w_organization_social`** anhaken
   (falls angeboten auch `r_organization_social`) → mit dem Admin-Konto bestätigen.
3. Es erscheinen ein **Access token** und – wenn LinkedIn es für die App freigibt – ein **Refresh token**.
4. **Organisations-ID:** Seite als Admin öffnen; die Zahl in der Adresse `linkedin.com/company/12345678/admin/` ist die ID.

> Schlüssel niemals per E-Mail, WhatsApp oder in den Chat schicken – nur in die GitHub-Secrets.

### 3. GitHub-Secrets anlegen
Repository → Settings → Secrets and variables → Actions → New repository secret:
- `LINKEDIN_ORG_ID` – die Zahl aus Schritt 2.4
- mit Refresh-Token (empfohlen, läuft ca. 1 Jahr): `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_REFRESH_TOKEN`
- ohne Refresh-Token: `LINKEDIN_ACCESS_TOKEN` (läuft nach ca. 60 Tagen ab und muss dann neu erzeugt werden)

Test: Actions → „Social-Autopilot“ → Run workflow mit dry_run. In `testlauf.txt` steht dann „OK LinkedIn-Zugang gültig“
und, falls vorhanden, bis wann der Refresh-Token gilt (auch in `state.json` unter `linkedin_refresh_token_expires`).

**Fehler:** Ein LinkedIn-Fehler hält Instagram/Facebook nicht auf. Der Lauf wird danach rot markiert (E-Mail von GitHub),
der Post wird aber nicht doppelt veröffentlicht. Fehlertext steht in `published/<post>.json` unter `linkedin_error`.


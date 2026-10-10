# Taxi Akbulut – Social-Autopilot

Postet automatisch Werbebilder auf Instagram (Feed + Story) und Facebook, 3× pro Woche (Mo/Mi/Fr 18:00), plus 1 Reel mit eigener Musik pro Woche (Sa 11:00).
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
- Die erste Planung startet am **Sonntag, 11.10.2026, 9:00 Uhr**, danach Mo/Mi/Fr 18:00. Liegt die Einrichtung später, werden überfällige Posts
  einzeln nachgeholt – einer pro Tag.

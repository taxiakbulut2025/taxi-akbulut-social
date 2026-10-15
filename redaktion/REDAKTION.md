# Redaktionsregeln für den Social-Autopilot

## Rhythmus
- Themen-Tage, jeweils 18:00 Uhr (Europe/Berlin), jeweils mit Story:
  - Montag: Taxi Tübingen (`category: taxi-tuebingen`) – Stadtfahrten, Bahnhof, Kartenzahlung, Online-Konto, Familienbetrieb
  - Dienstag: Krankenfahrten (`krankenfahrten`)
  - Mittwoch: Flughafentransfer Stuttgart (`flughafen`)
  - Donnerstag: Ferntaxi (`ferntaxi`)
  - Freitag: im Wechsel Event-Shuttle (`event-shuttle`) und Medizinkurier – Blut-/Medikamententransport (`medizinkurier`)
- 1 Reel pro Woche: Samstag 11:00 Uhr (`category: reel`).
- Sonntag 18:00: Chauffeurservice (`category: chauffeurservice`) – Zielgruppe Geschäftsleute, eigener Markenstil „AKBULUT. Fahrservice“ (siehe unten).
- Keine Werbe-Posts an Feiertagen mit Familienbezug: 24.–26.12., 31.12., 1.1., Ostersonntag/-montag. Diese Termine überspringen (der Themen-Tag fällt dann aus).
- Puffer: Für JEDE Kategorie muss die Warteschlange mindestens 3 Termine im Voraus gefüllt sein. Fehlt etwas, zuerst die Kategorie mit dem kleinsten Vorrat auffüllen (neue Motive im festgelegten Stil).
- Innerhalb einer Kategorie ähnliche Motive (z. B. zwei Rollstuhl-Motive, zwei Festpreis-Motive) mit mindestens 3 Wochen Abstand.
- Kein Motiv wiederholen, das in `queue/` oder `published/` schon vorkommt (Feld `motiv`, Überschrift).
- Übersicht aller Termine: `redaktion/plan.txt` – nach jeder Änderung aktualisieren.

## Reels (1× pro Woche, Samstag 11:00)
- Zusätzlich zu den Bild-Posts ein Reel pro Woche, samstags 11:00, aus dem stärksten Motiv der Woche.
- Format 1080 × 1920, 9 Sekunden, 30 fps. Vorlage: `vorlagen/reel-gelandet.html` (CSS-Animationen mit Verzögerung, Elemente erscheinen nacheinander).
- Sicherer Bereich: oben 200 px und unten 360 px frei lassen – dort liegen Instagram-Bedienelemente. „Online buchen | taxi-akbulut.de" als schwarze Pill IM sichtbaren Bereich, letzter Animationsschritt bei ca. 5,8 s.
- Musik: nur selbst erzeugt mit `generator/music.py` (keine fremden Songs, keine Lizenzmusik). Pro Reel anderen `--seed` und ggf. `--bpm` (100–120) wählen; `--pops` auf die Zeitpunkte erscheinender Elemente legen, `--chime` auf den Abschluss.
- Bauen: `(cd generator && npm install) && bash generator/make_reel.sh motive/<slug>-reel.html reels/<datum>-<slug>.mp4 --seed N --pops 2.0,3.5 --chime 5.8`
  Danach die erzeugte `reels/<datum>-<slug>-vorschau.jpg` mit dem Read-Tool prüfen (Endbild) und wieder löschen.
- Queue-Eintrag: `"type": "reel"`, `"video": "reels/<datum>-<slug>.mp4"` statt image/story_image.

## Bild (Stil festgelegt – siehe `vorlagen/`)
- Format 1080 × 1350 px (4:5), Schrift Archivo 500/700/900.
- Farben: Elfenbein #F4EFE3, Schwarz #121212, Gelb #F2C230; Grautöne #2B2924, #4A4740, #C9C3B6, #E6E0D2.
- Aufbau immer: Kopfzeile (TAXI-Badge + AKBULUT, rechts „Tübingen · seit 1986"), große Überschrift, ein visuelles Element, 1–2 Sätze, ggf. Kleingedrucktes, unten Leiste „Online buchen | taxi-akbulut.de".
- Hintergründe rotieren: hell → schwarz → gelb.
- Keine Telefonnummer als Handlungsaufruf. Keine Emojis im Bild. Keine Fotos fremder Marken oder Personen.
- Neue Motive als HTML-Fragment in `motive/<slug>.html` (Muster: Dateien in `vorlagen/`, Serie 4/5 = k*, f*, t*, e*, m*), dann rendern:
  `cd generator && npm install && cd .. && node generator/render.js motive/<slug>.html images/<datum>-<slug>.jpg`
  Der Renderer bricht ab, wenn Text überläuft – dann kürzen.
- Zu jedem Bild die Story-Version (9:16) erzeugen: `python3 generator/story.py images/<datum>-<slug>.jpg`

## Text (Bildunterschrift)
- Stimme: Sie-Form, Absender „wir", Hochdeutsch, ruhig und konkret. Keine Floskeln („zuverlässiger Partner", „maßgeschneidert", „egal ob").
- 40–110 Wörter, mindestens ein konkreter Fakt aus `fakten.md`. Nichts erfinden.
- Preise immer mit „Endpreis inkl. MwSt." und Stand. Bewertungen immer korrekt zugeordnet (siehe fakten.md).
- Höchstens ein Emoji, besser keins.

### SEO-Aufbau (Instagram-Suche liest Bildtext und Alt-Text)
1. Aufhänger + 1–2 Absätze Inhalt (Suchbegriff des Themas möglichst im ersten Satz).
2. Fester SEO-Satz der Kategorie:
   - taxi-tuebingen: „Taxi Akbulut ist Ihr Taxi in Tübingen, Familienbetrieb seit 1986."
   - krankenfahrten: „Krankenfahrten in Tübingen und Umgebung: Wir rechnen direkt mit Krankenkasse, Berufsgenossenschaft und Unfallkasse ab."
   - flughafen (auch Flughafen-Reels): „Flughafentransfer und Airport-Shuttle von Tübingen zum Flughafen Stuttgart (STR) und zurück, zum Festpreis."
   - ferntaxi: „Ferntaxi ab Tübingen: Langstreckenfahrten zu jedem Ziel in Deutschland."
   - event-shuttle: „Event-Shuttle in Tübingen und Umgebung für Hochzeit, Firmenfeier, Weihnachtsfeier und Messe."
   - chauffeurservice: „Chauffeurservice in Tübingen, Reutlingen und Stuttgart: Mercedes E- und V-Klasse mit Fahrer, auf Vorbestellung.“
   - medizinkurier: „Medizinischer Kurierdienst in Tübingen: Blutproben- und Medikamententransport für Praxen, Labore und Kliniken."
3. `Online buchen: taxi-akbulut.de (Link im Profil)`
4. GENAU 5 Hashtags (Instagram-Limit seit Dez. 2025): 3 Kern-Hashtags der Kategorie + 1 motivbezogener + `#TaxiAkbulut`.
   - taxi-tuebingen: #TaxiTübingen #Tübingen #Taxi + (z. B. #Kartenzahlung, #Kindersitz, #Familienbetrieb; sonst #TübingenCity)
   - krankenfahrten: #KrankenfahrtTübingen #Krankenfahrten #Krankenfahrt + (z. B. #Dialyse, #Reha, #Rollstuhl, #Arbeitsunfall; sonst #TaxiTübingen)
   - flughafen: #FlughafentransferStuttgart #AirportShuttleStuttgart #FlughafenStuttgart + (z. B. #Familienurlaub, #Geschäftsreise, #Frühflug; sonst #FlughafenshuttleStuttgart)
   - ferntaxi: #Ferntaxi #FerntaxiTübingen #Langstrecke + (z. B. #Zugausfall, #Gruppenreise; sonst #TaxiTübingen)
   - event-shuttle: #EventShuttle #ShuttleTübingen #Shuttleservice + (z. B. #Hochzeit, #Weihnachtsfeier, #MesseStuttgart; sonst #TaxiTübingen)
   - chauffeurservice: #Chauffeurservice #ChauffeurserviceStuttgart #Limousinenservice + (z. B. #Geschäftsreise, #Pünktlichkeit, #VKlasse) + **#AkbulutFahrservice** statt #TaxiAkbulut
   - medizinkurier: #Medizinkurier #MedizinkurierTübingen #Laborkurier + (z. B. #Blutproben, #Medikamententransport; sonst #Kurierdienst)
5. Feld `"alt_text"` (nur Bild-Posts): sachliche Bildbeschreibung mit Überschrift in Anführungszeichen, max. 1000 Zeichen.
6. Standort-Markierung setzt der Publisher automatisch (Facebook-Seite Taxi Akbulut Tübingen mit Adresse).

## Datei-Format eines Posts (`queue/<datum>-<slug>.json`)
```json
{
  "publish_at": "2026-12-14 18:00",
  "category": "krankenfahrten",
  "image": "images/2026-12-14-<slug>.jpg",
  "caption": "…",
  "alt_text": "Werbebild …: „Überschrift“ …",
  "instagram": true,
  "facebook": true,
  "story": true,
  "story_image": "stories/2026-12-14-<slug>.jpg",
  "motiv": "<slug>"
}
```

## Markenstil Chauffeurservice („AKBULUT. Fahrservice“)
- Nur für `category: chauffeurservice`. Vorlage: `vorlagen/chauffeur_build.py` (Funktionen frame/label/h1/body/items/cards).
- Hintergrund dunkel (radialer Verlauf #191929 → #030305), Gold #C9A227, Weiß, Grau #9CA3AF; Schrift Roboto 400/500/700/900; goldene Eckwinkel oben links/unten rechts.
- Kopf: Goldquadrat „A.“ + „AKBULUT.“ (Punkt gold), rechts „CHAUFFEURSERVICE“ gesperrt in Gold. Fuß: „TÜBINGEN · REUTLINGEN · STUTTGART“ + „ONLINE BUCHEN“ + taxi-akbulut.de.
- Überschrift endet mit goldenem Punkt. Kein Wort „Taxi“ im Bild. Gelb (#F2C230) hier nicht verwenden.
- Fotos nur echte eigene Fahrzeugfotos, abgedunkelt; keine Kundenmarken im Text.

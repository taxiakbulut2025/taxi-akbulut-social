# Redaktionsregeln für den Social-Autopilot

## Rhythmus
- Themen-Tage, jeweils 18:00 Uhr (Europe/Berlin), jeweils mit Story:
  - Montag: Taxi Tübingen (`category: taxi-tuebingen`) – Stadtfahrten, Bahnhof, Kartenzahlung, Online-Konto, Familienbetrieb
  - Dienstag: Krankenfahrten (`krankenfahrten`)
  - Mittwoch: Flughafentransfer Stuttgart (`flughafen`)
  - Donnerstag: Ferntaxi (`ferntaxi`)
  - Freitag: im Wechsel Event-Shuttle (`event-shuttle`) und Medizinkurier – Blut-/Medikamententransport (`medizinkurier`)
- 1 Reel pro Woche: Samstag 11:00 Uhr (`category: reel`).
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
- Schluss immer: `Online buchen: taxi-akbulut.de (Link im Profil)` + Leerzeile + `#Tübingen #TaxiTübingen #TaxiAkbulut` + 1–2 Themen-Hashtags.
- Höchstens ein Emoji, besser keins.

## Datei-Format eines Posts (`queue/<datum>-<slug>.json`)
```json
{
  "publish_at": "2026-12-14 18:00",
  "category": "krankenfahrten",
  "image": "images/2026-12-14-<slug>.jpg",
  "caption": "…",
  "instagram": true,
  "facebook": true,
  "story": true,
  "story_image": "stories/2026-12-14-<slug>.jpg",
  "motiv": "<slug>"
}
```

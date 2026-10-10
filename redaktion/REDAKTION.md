# Redaktionsregeln für den Social-Autopilot

## Rhythmus
- 3 Posts pro Woche: Montag, Mittwoch, Freitag, jeweils 18:00 Uhr (Europe/Berlin).
- Die Warteschlange (`queue/`) soll immer mindestens 2 Wochen (6 Posts) im Voraus gefüllt sein.
- Themen abwechseln: nie zwei Posts desselben Themas (Flughafen, Krankenfahrt, Vertrauen/Familie, Service/Online, Spezial) direkt hintereinander.
- Kein Motiv wiederholen, das in `queue/` oder `published/` schon vorkommt (Feld `motiv`, Überschrift).

## Bild (Stil festgelegt – siehe `vorlagen/`)
- Format 1080 × 1350 px (4:5), Schrift Archivo 500/700/900.
- Farben: Elfenbein #F4EFE3, Schwarz #121212, Gelb #F2C230; Grautöne #2B2924, #4A4740, #C9C3B6, #E6E0D2.
- Aufbau immer: Kopfzeile (TAXI-Badge + AKBULUT, rechts „Tübingen · seit 1986"), große Überschrift, ein visuelles Element, 1–2 Sätze, ggf. Kleingedrucktes, unten Leiste „Online buchen | taxi-akbulut.de".
- Hintergründe rotieren: hell → schwarz → gelb.
- Keine Telefonnummer als Handlungsaufruf. Keine Emojis im Bild. Keine Fotos fremder Marken oder Personen.
- Neue Motive als HTML-Fragment in `motive/<slug>.html` (Muster: Dateien in `vorlagen/`), dann rendern:
  `cd generator && npm install && cd .. && node generator/render.js motive/<slug>.html images/<datum>-<slug>.jpg`
  Der Renderer bricht ab, wenn Text überläuft – dann kürzen.

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
  "image": "images/2026-12-14-<slug>.jpg",
  "caption": "…",
  "instagram": true,
  "facebook": true,
  "motiv": "<slug>"
}
```

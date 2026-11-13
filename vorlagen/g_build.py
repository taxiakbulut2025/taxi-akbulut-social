"""Baut die Krankenfahrt-Serie g01–g05 im Hausstil (Archivo, Elfenbein/Schwarz/Gelb)."""
T = {
 "hell":  dict(bg="#F4EFE3", fg="#121212", sub="#4A4740", eye="#4A4740", mbg="#F2C230", mfg="#121212",
               cbg="#121212", cfg="#F4EFE3", acc="#F2C230", fbg="#F2C230", ffg="#121212", bbg="#F2C230", bfg="#121212"),
 "schwarz": dict(bg="#121212", fg="#F4EFE3", sub="#C9C3B6", eye="#F2C230", mbg="#F2C230", mfg="#121212",
               cbg="#2A2926", cfg="#F4EFE3", acc="#F2C230", fbg="#F2C230", ffg="#121212", bbg="#F2C230", bfg="#121212"),
 "gelb":  dict(bg="#F2C230", fg="#121212", sub="#2B2924", eye="#2B2924", mbg="#121212", mfg="#F2C230",
               cbg="#FFFFFF", cfg="#121212", acc="#121212", fbg="#121212", ffg="#F4EFE3", bbg="#121212", bfg="#F2C230"),
}
def mark(t, s): return f'<span style="background: {t["mbg"]}; color: {t["mfg"]}; padding: 0 16px 6px; white-space: nowrap">{s}</span>'
def cards(t, items, cols, size=32):
    h = "".join(f'<div style="background: {t["cbg"]}; color: {t["cfg"]}; border-radius: 18px; padding: 26px 26px; display: flex; flex-direction: column; gap: 12px"><span style="font-weight: 900; font-size: 30px; color: {t["acc"]}">✓</span><span style="font-weight: 700; font-size: {size}px; line-height: 1.2">{i}</span></div>' for i in items)
    return f'<div style="display: grid; grid-template-columns: repeat({cols}, minmax(0, 1fr)); gap: 14px">{h}</div>'
def para(t, s, size=36): return f'<p style="margin: 0; font-weight: 500; font-size: {size}px; line-height: 1.35; color: {t["sub"] if t["bg"]!="#121212" else "#F4EFE3"}; max-width: 880px">{s}</p>'
def frame(theme, eyebrow, h1, h1size, middle, small, foot_l="Online buchen"):
    t = T[theme]
    return f'''<div style="width: 1080px; height: 1350px; box-sizing: border-box; background: {t["bg"]}; color: {t["fg"]}; font-family: 'Archivo', sans-serif; display: flex; flex-direction: column; padding: 88px; position: relative; overflow: hidden">
<div style="display: flex; justify-content: space-between; align-items: center">
<div style="display: flex; align-items: center; gap: 18px">
<div style="width: 64px; height: 40px; background: {t["bbg"]}; color: {t["bfg"]}; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 15px; letter-spacing: 2px">TAXI</div>
<div style="font-weight: 900; font-size: 34px; letter-spacing: 1px">AKBULUT</div>
</div>
<div style="font-weight: 500; font-size: 24px; color: {t["sub"]}">Tübingen · seit 1986</div>
</div>
<div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center; gap: 40px">
<div style="font-weight: 700; font-size: 28px; letter-spacing: 3px; color: {t["eye"]}">{eyebrow}</div><h1 style="margin: 0; font-weight: 900; font-size: {h1size}px; line-height: 1.04; letter-spacing: -3px">{h1}</h1>{middle}
</div>
<div style="font-weight: 500; font-size: 20px; color: {t["sub"]}; margin-bottom: 28px">{small}</div>
<div style="background: {t["fbg"]}; color: {t["ffg"]}; margin: 0 -88px -88px; padding: 44px 88px; display: flex; justify-content: space-between; align-items: center">
<div style="font-weight: 900; font-size: 40px">{foot_l}</div>
<div style="font-weight: 700; font-size: 40px">taxi-akbulut.de</div>
</div>
</div>
'''
ZZ = "Bei gesetzlich Krankenversicherten kann die gesetzliche Zuzahlung anfallen."
M = {}
t = T["hell"]
M["g01-krankenfahrten-tuebingen"] = frame("hell", "KRANKENFAHRTEN TÜBINGEN",
    "Krankenfahrten<br>in " + mark(t, "Tübingen."), 112,
    para(t, "Direktabrechnung mit Ihrer Krankenkasse.") + cards(t, ["Abholung an der Wohnungstür", "Begleitung bis in Praxis oder Ambulanz", "Serienfahrten: Dialyse, Onkologie, Reha"], 3, 30), ZZ)
t = T["schwarz"]
M["g02-chemo-strahlentherapie"] = frame("schwarz", "KRANKENFAHRTEN ZU DEN TÜBINGER KLINIKEN",
    "Fahrten zur<br>Chemo- und<br>" + mark(t, "Strahlentherapie."), 96,
    para(t, "Wir fahren Sie in diese Kliniken:", 32) + cards(t, ["Crona Kliniken", "Medizinische Klinik", "Frauenklinik", "Hautklinik"], 2, 34),
    "Direktabrechnung mit gesetzlichen Krankenkassen. " + ZZ)
t = T["gelb"]
M["g03-entlassfahrten"] = frame("gelb", "HEIMFAHRT NACH DEM KLINIKAUFENTHALT",
    "Entlassfahrten<br>" + mark(t, "ab der Klinik."), 108,
    para(t, "Direktabrechnung mit gesetzlichen Krankenkassen.") + cards(t, ["Abholung direkt an der Klinik", "Faltbarer Rollstuhl fährt mit", "Heimfahrten deutschlandweit"], 3, 30),
    ZZ + " Für Fahrten im Sitzen.")
t = T["hell"]
M["g04-kinder-jugendpsychiatrie"] = frame("hell", "KRANKENFAHRTEN FÜR KINDER UND JUGENDLICHE",
    "Fahrten zur Kinder-<br>und Jugend-<br>" + mark(t, "psychiatrie."), 92,
    cards(t, ["Live-Tracking-Link für die Eltern", "Direktabrechnung mit den gesetzlichen Krankenkassen"], 2, 34),
    "Kinder- und Jugendpsychiatrie Tübingen. " + ZZ)
t = T["schwarz"]
M["g05-genehmigung-check"] = frame("schwarz", "KRANKENFAHRT · ONLINE-CHECK",
    "Genehmigung<br>" + mark(t, "nötig?"), 116,
    para(t, "Höchstens 5 Fragen, Ergebnis sofort, ohne Anmeldung. Eines von drei Ergebnissen:", 34)
    + cards(t, ["Genehmigungs&shy;frei", "Antrag nötig", "Keine Übernahme"], 3, 32)
    + f'<div style="font-weight: 900; font-size: 36px; white-space: nowrap; color: #F2C230">taxi-akbulut.de/krankenfahrten-tuebingen</div>',
    "Grundlage: § 60 SGB V und Krankentransport-Richtlinie. Im Einzelfall entscheidet Ihre Krankenkasse.", "Jetzt prüfen")
if __name__ == "__main__":
    for slug, html in M.items():
        open(f"motive/{slug}.html", "w", encoding="utf-8").write(html); print(slug)

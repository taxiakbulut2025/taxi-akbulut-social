"""LinkedIn-Spur (seit 29.10.2026): eigene Werbebilder nur für die LinkedIn-Unternehmensseite.

- li-morgen (Mo/Mi/Fr 08:00): Medizinischer Kurierdienst im Taxi-Akbulut-Stil (Archivo, Elfenbein/Schwarz/Gelb),
  jeweils mit Linien-Icon.
- li-abend  (Mo/Mi/Fr 19:00): Chauffeurservice – nur Mercedes-Benz V-Klasse – im Markenstil
  „AKBULUT. Chauffeur Service" (Roboto, Gold/Schwarz, Wortmarke aus vorlagen/brand/), jeweils mit Linien-Icon.

Aufruf: python3 vorlagen/linkedin_build.py  → schreibt motive/<slug>.html (1080×1350).
Rendern mit Archivo + Roboto (siehe redaktion/REDAKTION.md, Abschnitt LinkedIn).
Fakten ausschließlich aus redaktion/fakten.md.
"""
import base64
import os

D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(D), 'motive')
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- Icons (Linien, viewBox 200×200)
def svg(inner, color, size=300, sw=8, vb='0 0 200 200'):
    return (f'<svg width="{size}" height="{size}" viewBox="{vb}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">{inner}</svg>')

def snow(cx, cy, r):
    s = ''
    for a, b in ((0, 1), (0.866, 0.5), (0.866, -0.5)):
        s += f'<line x1="{cx - a * r}" y1="{cy - b * r}" x2="{cx + a * r}" y2="{cy + b * r}"/>'
    return s

I = {
    # Kühlbox mit Schneeflocke
    'box': '<rect x="30" y="70" width="140" height="95" rx="10"/><rect x="24" y="52" width="152" height="22" rx="6"/>'
           '<path d="M75 52 V38 H125 V52"/>' + snow(100, 117, 26),
    # Kühlschrank → Kühlbox
    'fridge_box': '<rect x="14" y="30" width="62" height="140" rx="8"/><line x1="14" y1="78" x2="76" y2="78"/>'
                  '<line x1="64" y1="50" x2="64" y2="62"/><line x1="64" y1="92" x2="64" y2="112"/>'
                  '<path d="M88 100 H118 M106 88 L118 100 L106 112"/>'
                  '<rect x="130" y="92" width="62" height="56" rx="6"/><rect x="126" y="80" width="70" height="14" rx="4"/>' + snow(161, 120, 14),
    # Praxis / Labor / Klinik
    'praxis': '<rect x="40" y="40" width="120" height="120" rx="14"/><path d="M100 70 V130 M70 100 H130"/>',
    'labor': '<path d="M80 30 H120 M88 30 V82 L48 160 Q44 170 56 170 H144 Q156 170 152 160 L112 82 V30"/><path d="M66 128 H134"/>',
    'klinik': '<rect x="36" y="56" width="128" height="114" rx="6"/><path d="M80 30 H120 V56 M100 36 V50 M93 43 H107"/>'
              '<path d="M78 92 V142 M122 92 V142 M78 117 H122"/>',
    # Kalender mit Haken
    'kalender': '<rect x="28" y="40" width="144" height="132" rx="12"/><line x1="28" y1="78" x2="172" y2="78"/>'
                '<line x1="64" y1="26" x2="64" y2="54"/><line x1="136" y1="26" x2="136" y2="54"/>'
                '<path d="M66 124 L90 146 L136 102"/>',
    # Reagenzglas
    'probe': '<path d="M78 24 H122 M86 24 V150 Q86 176 100 176 Q114 176 114 150 V24"/><path d="M86 110 H114"/>',
    # Medikament + Probe
    'zwei': '<rect x="22" y="70" width="70" height="36" rx="18" transform="rotate(-35 57 88)"/>'
            '<line x1="57" y1="68" x2="57" y2="108" transform="rotate(-35 57 88)"/>'
            '<path d="M128 40 H164 M134 40 V146 Q134 166 146 166 Q158 166 158 146 V40"/><path d="M134 112 H158"/>',
    # Lenkrad
    'lenkrad': '<circle cx="100" cy="100" r="74"/><circle cx="100" cy="100" r="16"/>'
               '<path d="M30 92 Q100 70 170 92 M100 116 V172"/>',
    # Kofferraum (durchgestrichen) – Kühlbox (Haken)
    'nicht_kofferraum': '<rect x="14" y="70" width="70" height="60" rx="6"/><line x1="8" y1="150" x2="90" y2="50"/>'
                        '<rect x="116" y="76" width="70" height="56" rx="6"/><rect x="112" y="64" width="78" height="14" rx="4"/>'
                        + snow(151, 104, 13) + '<path d="M132 160 L146 172 L172 146"/>',
    # Drei Stationen
    'stationen': '<circle cx="34" cy="100" r="18"/><circle cx="100" cy="100" r="18"/><circle cx="166" cy="100" r="18"/>'
                 '<line x1="52" y1="100" x2="82" y2="100"/><line x1="118" y1="100" x2="148" y2="100"/>',
}

V = {  # Chauffeur-Icons (Gold)
    'van': ('<path d="M14 112 V74 Q16 56 36 52 L82 28 H262 Q284 28 286 52 L288 112 Z"/>'
            '<path d="M92 40 L60 66 H124 V40 Z M138 40 V66 H190 V40 Z M204 40 V66 H262 Q270 66 270 56 V40 Z"/>'
            '<circle cx="72" cy="116" r="22"/><circle cx="234" cy="116" r="22"/>', '0 0 300 150'),
    'sitz': ('<path d="M66 30 Q56 30 56 44 L64 118 Q66 130 80 130 H132"/><path d="M64 118 L60 160 M130 130 L140 168 M58 168 H146"/>'
             '<path d="M80 130 Q86 106 112 106 H140 Q152 106 152 118 V130"/>', '0 0 200 200'),
    'koffer': ('<rect x="40" y="58" width="120" height="112" rx="12"/><path d="M76 58 V36 H124 V58"/>'
               '<line x1="74" y1="80" x2="74" y2="148"/><line x1="126" y1="80" x2="126" y2="148"/>'
               '<circle cx="62" cy="180" r="6"/><circle cx="138" cy="180" r="6"/>', '0 0 200 200'),
    'flug': ('<path d="M20 120 L180 50 Q196 46 188 62 L120 120 L92 172 L82 168 L94 126 L52 134 L40 150 L30 146 L36 126 Z"/>', '0 0 200 200'),
    'messe': ('<path d="M20 170 V96 L100 48 L180 96 V170 Z"/><rect x="80" y="120" width="40" height="50"/>'
              '<path d="M100 48 V18 L128 26 L100 34"/><path d="M44 120 H64 M136 120 H156"/>', '0 0 200 200'),
    'uhr': ('<circle cx="100" cy="104" r="70"/><path d="M100 64 V104 L128 122"/><path d="M84 22 H116"/>', '0 0 200 200'),
    'preis': ('<path d="M30 102 L100 32 H168 V100 L98 170 Z"/><circle cx="136" cy="64" r="12"/>', '0 0 200 200'),
    'schild': ('<rect x="20" y="58" width="160" height="92" rx="8"/><path d="M60 58 L100 26 L140 58"/>'
               '<path d="M48 92 H152 M48 118 H120"/>', '0 0 200 200'),
    'staedte': ('<path d="M40 150 Q100 40 160 150"/><circle cx="40" cy="150" r="14"/><circle cx="100" cy="76" r="14"/><circle cx="160" cy="150" r="14"/>', '0 0 200 200'),
}


# ---------------------------------------------------------------- Medizin (Taxi-Akbulut-Stil)
THEMES = {
    'hell':    {'bg': '#F4EFE3', 'fg': '#121212', 'acc': '#121212', 'hl': '#121212', 'sub': '#4A4740', 'lab': '#4A4740',
                'bar': '#F2C230', 'bar_fg': '#121212', 'badge': '#F2C230', 'badge_fg': '#121212', 'chip': '#121212', 'chip_fg': '#F4EFE3'},
    'schwarz': {'bg': '#121212', 'fg': '#F4EFE3', 'acc': '#F2C230', 'hl': '#F2C230', 'sub': '#E6E0D2', 'lab': '#F2C230',
                'bar': '#F2C230', 'bar_fg': '#121212', 'badge': '#F2C230', 'badge_fg': '#121212', 'chip': '#F2C230', 'chip_fg': '#121212'},
    'gelb':    {'bg': '#F2C230', 'fg': '#121212', 'acc': '#121212', 'hl': '#121212', 'sub': '#2B2924', 'lab': '#2B2924',
                'bar': '#121212', 'bar_fg': '#F4EFE3', 'badge': '#121212', 'badge_fg': '#F2C230', 'chip': '#121212', 'chip_fg': '#F2C230'},
}

def med(theme, h1, body, icon, h1_size=124,
        small='Medizinischer Kurierdienst für Praxen, Labore und Kliniken. Konditionen auf Anfrage.', chips=None, extra=''):
    t = THEMES[theme]
    ic = svg(I[icon], t['acc'], 300, 8)
    ch = ''
    if chips:
        ch = '<div style="display:flex;flex-wrap:wrap;gap:14px">' + ''.join(
            f'<div style="background:{t["chip"]};color:{t["chip_fg"]};border-radius:999px;padding:14px 26px;font-weight:800;font-size:27px">{c}</div>'
            for c in chips) + '</div>'
    return f'''<div style="width:1080px;height:1350px;box-sizing:border-box;background:{t['bg']};color:{t['fg']};font-family:'Archivo',sans-serif;display:flex;flex-direction:column;padding:88px;position:relative;overflow:hidden">
<div style="display:flex;justify-content:space-between;align-items:center">
<div style="display:flex;align-items:center;gap:18px">
<div style="width:64px;height:40px;background:{t['badge']};color:{t['badge_fg']};border-radius:6px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:15px;letter-spacing:2px">TAXI</div>
<div style="font-weight:900;font-size:34px;letter-spacing:1px">AKBULUT</div>
</div>
<div style="font-weight:500;font-size:24px;color:{t['sub']}">Tübingen · seit 1986</div>
</div>
<div style="flex-grow:1;display:flex;flex-direction:column;justify-content:center;gap:36px">
<div style="display:flex;justify-content:space-between;align-items:flex-end">
<div style="font-weight:700;font-size:28px;letter-spacing:3px;color:{t['lab']}">MEDIZINKURIER TÜBINGEN</div>
</div>
<div style="display:flex;align-items:center;justify-content:flex-start">{ic}</div>
<h1 style="margin:0;font-weight:900;font-size:{h1_size}px;line-height:1.02;letter-spacing:-3px">{h1}</h1>
<p style="margin:0;font-weight:500;font-size:34px;line-height:1.36;color:{t['sub']};max-width:880px">{body}</p>{ch}{extra}
</div>
<div style="font-weight:500;font-size:20px;color:{t['sub']};margin-bottom:28px">{small}</div>
<div style="background:{t['bar']};color:{t['bar_fg']};margin:0 -88px -88px;padding:44px 88px;display:flex;justify-content:space-between;align-items:center">
<div style="font-weight:900;font-size:40px">Kurier anfragen</div>
<div style="font-weight:700;font-size:40px">taxi-akbulut.de</div>
</div>
</div>'''

def hl(t, theme):  # Schlusswort hervorheben (wie m01: gelbes Wort auf Schwarz)
    return f'<span style="color:{THEMES[theme]["hl"]}">{t}</span>'

def steps(lst, theme):
    t = THEMES[theme]
    return '<div style="display:flex;flex-direction:column;gap:16px">' + ''.join(
        f'<div style="display:flex;align-items:center;gap:22px"><div style="width:58px;height:58px;border-radius:50%;background:{t["chip"]};color:{t["chip_fg"]};'
        f'display:flex;align-items:center;justify-content:center;font-weight:900;font-size:28px;flex-shrink:0">{i + 1}</div>'
        f'<div style="font-weight:700;font-size:34px">{s}</div></div>' for i, s in enumerate(lst)) + '</div>'


# ---------------------------------------------------------------- V-Klasse (AKBULUT. Chauffeur Service)
G, W, GR = '#C9A227', '#FFFFFF', '#9CA3AF'
LOGO = 'data:image/png;base64,' + base64.b64encode(open(os.path.join(D, 'brand', 'akbulut-chauffeur-wortmarke-dunkel.png'), 'rb').read()).decode()
dot = f'<span style="color:{G}">.</span>'

def vframe(label, h1, body, icon, h1_size=100, extra='', foot=''):
    path, vb = V[icon]
    w = 520 if icon == 'van' else 260
    ic = f'<svg width="{w}" height="{int(w * (150 / 300 if icon == "van" else 1))}" viewBox="{vb}" fill="none" stroke="{G}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">{path}</svg>'
    b = f'border-color:{G};border-style:solid;width:86px;height:86px;position:absolute'
    fd = f'<div style="font-weight:400;font-size:19px;color:#6B7280;margin-bottom:22px">{foot}</div>' if foot else ''
    return f'''<div style="width:1080px;height:1350px;box-sizing:border-box;position:relative;overflow:hidden;background:radial-gradient(ellipse 75% 60% at 50% 48%,#191929 0%,#0B0B13 55%,#030305 100%);color:{W};font-family:'Roboto',sans-serif;display:flex;flex-direction:column;padding:92px 104px 92px">
<div style="{b};border-width:4px 0 0 4px;left:44px;top:44px"></div><div style="{b};border-width:0 4px 4px 0;right:44px;bottom:44px"></div>
<div style="display:flex;justify-content:space-between;align-items:center;position:relative">
<img src="{LOGO}" style="height:128px;width:auto;display:block" alt="">
<div style="font-weight:500;font-size:18px;letter-spacing:6px;color:{G}">MERCEDES-BENZ V-KLASSE</div>
</div>
<div style="flex-grow:1;display:flex;flex-direction:column;justify-content:center;gap:34px;position:relative">
<div>{ic}</div>
<div style="font-weight:500;font-size:21px;letter-spacing:7px;color:{G}">{label}</div>
<h1 style="margin:0;font-weight:900;font-size:{h1_size}px;line-height:1.0;letter-spacing:-2px">{h1}</h1>
<div style="width:120px;height:3px;background:{G}"></div>
<p style="margin:0;font-weight:400;font-size:33px;line-height:1.42;color:#D1D5DB;max-width:860px">{body}</p>{extra}
</div>
<div style="position:relative">{fd}
<div style="height:1px;background:linear-gradient(90deg,rgba(201,162,39,0),{G} 50%,rgba(201,162,39,0));margin-bottom:26px"></div>
<div style="display:flex;justify-content:space-between;align-items:center">
<div style="font-weight:500;font-size:17px;letter-spacing:5px;color:{GR}">TÜBINGEN · REUTLINGEN · STUTTGART</div>
<div style="display:flex;align-items:center;gap:14px"><span style="border:2px solid {G};color:{G};border-radius:999px;padding:9px 18px;font-weight:700;font-size:16px;letter-spacing:3px">ONLINE BUCHEN</span><span style="font-weight:700;font-size:24px">taxi-akbulut.de</span></div>
</div></div>
</div>'''

def vcards(lst):
    c = ''.join(f'<div style="flex:1;border:1px solid #3A3320;background:rgba(201,162,39,.06);border-radius:6px;padding:26px 28px">'
                f'<div style="font-weight:500;font-size:16px;letter-spacing:5px;color:{G};margin-bottom:12px">V-KLASSE</div>'
                f'<div style="font-weight:900;font-size:40px;line-height:1.05;margin-bottom:10px">{a}</div>'
                f'<div style="font-weight:400;font-size:26px;color:#D1D5DB">{b}</div></div>' for a, b in lst)
    return f'<div style="display:flex;gap:22px">{c}</div>'


M = {
    # ---- Medizinkurier (morgens)
    'li-m11-kuehlschrank-kuehlbox': med('schwarz', 'Vom Kühlschrank<br>in die ' + hl('Kühlbox.', 'schwarz'),
        'Wir holen Proben und Medikamente in Ihrer Praxis ab und transportieren sie gekühlt in ThermoSecure-Kühlboxen.', 'fridge_box', 112),
    'li-m12-praxen-labore-kliniken': med('hell', 'Praxen.<br>Labore.<br>Kliniken.',
        'Für sie fährt unser medizinischer Kurierdienst in Tübingen und Umgebung. Blutproben, Laborproben und Medikamente, gekühlt.', 'labor', 128),
    'li-m13-sie-bestimmen-den-takt': med('gelb', 'Sie bestimmen<br>den Takt.',
        'Regelmäßige Touren stimmen wir mit Ihrer Praxis oder Ihrem Labor ab: Tage, Abholpunkte, Ablauf.', 'kalender', 128),
    'li-m14-abgeholt-gekuehlt-uebergeben': med('schwarz', 'Abgeholt.<br>Gekühlt.<br>' + hl('Übergeben.', 'schwarz'),
        'Vom Probenbehälter in die ThermoSecure-Kühlbox bis zur Übergabe im Labor.', 'stationen', 124),
    'li-m15-kein-kofferraum': med('hell', 'Eine Kühlbox ist<br>kein Kofferraum.',
        'Proben und Medikamente fahren bei uns nicht lose mit. Sie reisen gekühlt in ThermoSecure-Kühlboxen.', 'nicht_kofferraum', 104),
    'li-m16-zwei-frachten': med('gelb', 'Zwei Frachten.<br>Eine Kühlbox.',
        'Laborproben auf dem Weg ins Labor, Medikamente auf dem Weg zur Klinik. Beides transportieren wir gekühlt.', 'zwei', 120,
        chips=['Blutproben', 'Laborproben', 'Medikamente']),
    'li-m17-so-fangen-wir-an': med('schwarz', 'So fangen<br>wir ' + hl('an.', 'schwarz'),
        'Konditionen auf Anfrage.', 'probe', 128,
        extra=steps(['Anfrage über taxi-akbulut.de', 'Tour und Abholpunkte abstimmen', 'Wir holen gekühlt ab'], 'schwarz')),
    'li-m18-inhaber-fahren': med('hell', 'Die Inhaber<br>fahren selbst.',
        'Taxi Akbulut ist ein Familienbetrieb aus Tübingen, seit 1986 in zweiter Generation. Die Inhaber sitzen bis heute selbst am Steuer.', 'lenkrad', 124),
    'li-m19-proben-in-der-box': med('gelb', 'Ihre Proben<br>haben einen<br>festen Platz.',
        'In der ThermoSecure-Kühlbox statt auf dem Beifahrersitz. Gekühlt von der Abholung bis zur Übergabe.', 'box', 112),

    # ---- Chauffeurservice V-Klasse (abends)
    'li-v01-raum-fuer-den-termin': vframe('LUXUS-LINER', f'Raum für den<br>Termin danach{dot}',
        'Unser V-Klasse Luxus-Liner hat bewusst nur vier Sitze. So bleibt im Fond Platz, um sich vorzubereiten.', 'sitz', 100),
    'li-v02-sieben-plaetze': vframe('BUSINESS LINER', f'Sieben Plätze.<br>Sieben Koffer{dot}',
        'Die V-Klasse Business Liner nimmt bis zu 7 Fahrgäste mit 7 Koffern und 4 Handgepäckstücken mit. Die Delegation reist gemeinsam.', 'koffer', 104),
    'li-v03-gate-meeting': vframe('FLUGHAFEN STUTTGART', f'Vom Gate<br>ins Meeting{dot}',
        'Wir verfolgen Ihren Flug live. Landet er früher oder später, steht die V-Klasse trotzdem bereit, wenn Sie herauskommen.', 'flug', 108),
    'li-v04-messe-stuttgart': vframe('MESSE STUTTGART', f'Zur Messe.<br>Gemeinsam{dot}',
        'Bis zu 7 Gäste pro Fahrt in der V-Klasse. Größere Gruppen fahren wir in mehreren Fahrten, den Preis vereinbaren wir vorab.', 'messe', 112),
    'li-v05-puenktlich-garantie': vframe('PÜNKTLICHKEITSGARANTIE', f'Pünktlich.<br>Mit Garantie{dot}',
        'Kommen wir zu spät, erhalten Sie eine Gutschrift. So ernst nehmen wir Ihren Termin.', 'uhr', 112,
        foot='Bedingungen der Pünktlichkeitsgarantie auf taxi-akbulut.de'),
    'li-v06-preis-vorab': vframe('TRANSPARENZ', f'Der Preis steht<br>vor der Fahrt{dot}',
        'Wir vereinbaren den Preis vorab. Sie buchen online und zahlen mit Karte.', 'preis', 100),
    'li-v07-zwei-modelle': vframe('FAHRZEUGE', f'Zwei Modelle.<br>Eine Klasse{dot}',
        'Für die Reise zu viert oder die ganze Delegation.', 'van', 104,
        extra=vcards([('Luxus-Liner', '4 Sitze, viel Raum'), ('Business Liner', 'bis 7 Fahrgäste')])),
    'li-v08-gaeste-empfangen': vframe('ABHOLUNG MIT NAMENSSCHILD', f'Ihre Gäste<br>werden erwartet{dot}',
        'Auf Wunsch empfängt Ihr Fahrer Ihre Gäste mit Namensschild in der Ankunftshalle.', 'schild', 104,
        foot='Namensschild gegen Aufpreis.'),
    'li-v09-drei-staedte': vframe('TÜBINGEN · REUTLINGEN · STUTTGART', f'Drei Städte.<br>Eine Buchung{dot}',
        'Vom Büro in Tübingen zum Termin in Reutlingen und weiter nach Stuttgart: eine Buchung, eine V-Klasse.', 'staedte', 108),
}

if __name__ == '__main__':
    for k, v in M.items():
        open(os.path.join(OUT, k + '.html'), 'w', encoding='utf-8').write(v)
    print(len(M), 'Motive geschrieben')

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
        small='Medizinischer Kurierdienst für Praxen, Labore und Kliniken. Konditionen auf Anfrage.', chips=None, extra='', big=None):
    t = THEMES[theme]
    ic = svg(I[icon], t['acc'], 300, 8) if icon else ''
    if big:  # große Zahl statt Icon
        ic = f'<div style="font-weight:900;font-size:230px;line-height:.85;letter-spacing:-8px;color:{t["acc"]}">{big}</div>'
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

def vframe(label, h1, body, icon, h1_size=100, extra='', foot='', big=None):
    path, vb = V[icon] if icon in V else (I.get(icon, ''), '0 0 200 200')
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
<div>{big_html(big) if big else ic}</div>
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

def big_html(t):
    return f'<div style="font-weight:900;font-size:230px;line-height:.82;letter-spacing:-8px;color:{G}">{t}</div>'

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

# ================================================================ Serie 2 (Nov 2026 – Jan 2027)
I.update({
    'verband': '<path d="M100 22 L164 46 V100 Q164 150 100 178 Q36 150 36 100 V46 Z"/><path d="M70 100 L92 122 L132 80"/>',
    'stern': '<path d="M100 24 L122 74 L176 78 L134 112 L148 166 L100 138 L52 166 L66 112 L24 78 L78 74 Z"/>',
    'liste': '<rect x="40" y="32" width="120" height="146" rx="10"/><path d="M76 32 V20 H124 V32"/>'
             '<path d="M62 74 L72 84 L88 66 M100 76 H138 M62 112 L72 122 L88 104 M100 114 H138 M62 150 L72 160 L88 142 M100 152 H138"/>',
    'pille': '<rect x="30" y="70" width="140" height="60" rx="30" transform="rotate(-30 100 100)"/>'
             '<line x1="100" y1="64" x2="100" y2="136" transform="rotate(-30 100 100)"/>',
    'tropfen': '<path d="M100 22 Q150 90 150 122 A50 50 0 0 1 50 122 Q50 90 100 22 Z"/><path d="M80 128 Q82 146 100 150"/>',
    'stetho': '<path d="M56 24 V80 Q56 116 90 116 Q124 116 124 80 V24"/><path d="M90 116 V140 Q90 172 124 172 Q152 172 152 144 V128"/>'
              '<circle cx="152" cy="112" r="16"/><path d="M46 24 H66 M114 24 H134"/>',
    'haus': '<path d="M28 96 L100 34 L172 96"/><path d="M48 80 V170 H152 V80"/><rect x="86" y="118" width="28" height="52"/>',
    'pin': '<path d="M100 178 Q44 116 44 78 A56 56 0 0 1 156 78 Q156 116 100 178 Z"/><circle cx="100" cy="78" r="20"/>',
    'tausch': '<path d="M34 70 H156 M132 46 L156 70 L132 94"/><path d="M166 132 H44 M68 108 L44 132 L68 156"/>',
    'sprechen': '<path d="M24 40 H128 V108 H68 L44 130 V108 H24 Z"/><path d="M146 76 H176 V144 H160 V164 L140 144 H86 V126"/>',
})
V.update({
    'glas': ('<path d="M52 30 H96 L90 86 Q86 104 74 104 Q62 104 58 86 Z M74 104 V160 M54 164 H94"/>'
             '<path d="M114 42 H158 L150 98 Q146 116 134 116 Q122 116 118 98 Z M134 116 V168 M114 172 H154"/>'
             '<path d="M100 14 V30 M84 20 L90 32 M116 20 L110 32"/>', '0 0 200 200'),
    'tasse': ('<path d="M34 76 H138 V112 Q138 162 86 162 Q34 162 34 112 Z"/><path d="M138 88 Q172 88 172 110 Q172 132 138 128"/>'
              '<path d="M24 176 H148"/><path d="M70 30 Q60 44 70 58 M96 30 Q86 44 96 58"/>', '0 0 200 200'),
    'zug': ('<rect x="46" y="22" width="108" height="132" rx="22"/><path d="M46 92 H154"/><rect x="66" y="40" width="68" height="36" rx="6"/>'
            '<circle cx="72" cy="122" r="8"/><circle cx="128" cy="122" r="8"/><path d="M66 154 L46 182 M134 154 L154 182"/>', '0 0 200 200'),
    'handy': ('<rect x="56" y="18" width="88" height="164" rx="14"/><path d="M88 34 H112"/><path d="M76 102 L94 120 L126 86"/>', '0 0 200 200'),
    'parken': ('<circle cx="100" cy="100" r="74"/><path d="M80 146 V56 H108 Q134 56 134 82 Q134 108 108 108 H80"/><line x1="48" y1="152" x2="152" y2="48"/>', '0 0 200 200'),
    'hotel': ('<rect x="42" y="30" width="116" height="148" rx="4"/><path d="M68 58 H84 M116 58 H132 M68 88 H84 M116 88 H132 M68 118 H84 M116 118 H132"/>'
              '<rect x="86" y="140" width="28" height="38"/>', '0 0 200 200'),
    'zwei_vans': ('<path d="M10 74 V52 Q12 40 26 38 L56 22 H130 Q144 22 146 38 L148 74 Z"/><circle cx="46" cy="76" r="12"/><circle cx="122" cy="76" r="12"/>'
                  '<path d="M152 140 V118 Q154 106 168 104 L198 88 H272 Q286 88 288 104 L290 140 Z"/><circle cx="188" cy="142" r="12"/><circle cx="264" cy="142" r="12"/>', '0 0 300 160'),
    'personen': ('<circle cx="70" cy="62" r="24"/><path d="M28 170 V138 Q28 104 70 104 Q112 104 112 138 V170"/>'
                 '<circle cx="138" cy="76" r="20"/><path d="M106 170 V146 Q106 116 138 116 Q170 116 170 146 V170"/>', '0 0 200 200'),
})
RAT2 = 'Gesamtnote aller Bewertungen auf ProvenExpert · Stand: Oktober 2026'
M.update({
    # ---- Medizinkurier, Serie 2
    'li-m20-fuer-praxen': med('hell', 'Für Praxen.', 'Wir holen Blutproben und Laborproben in Ihrer Praxis ab und bringen sie gekühlt ins Labor. Regelmäßige Touren nach Absprache.', 'praxis', 150),
    'li-m21-gekuehlt-ab-praxistuer': med('schwarz', 'Gekühlt ab der<br>' + hl('Praxistür.', 'schwarz'), 'Die Probe wandert bei der Abholung direkt in die ThermoSecure-Kühlbox. Dort bleibt sie bis zur Übergabe.', 'box', 116),
    'li-m22-blutproben': med('gelb', 'Blutproben.', 'Wir transportieren Blutproben aus Praxen und Kliniken gekühlt in ThermoSecure-Kühlboxen ins Labor.', 'tropfen', 150),
    'li-m23-taxiverband': med('hell', 'Mitglied im<br>Tübinger<br>Taxiverband.', 'Taxi Akbulut ist ein Tübinger Familienbetrieb seit 1986 und Mitglied im Tübinger Taxiverband. Auch unser Kurierdienst kommt aus diesem Betrieb.', 'verband', 112),
    'li-m24-fuer-labore': med('schwarz', 'Für ' + hl('Labore.', 'schwarz'), 'Proben aus den Praxen Ihrer Region bringen wir gekühlt zu Ihnen. Touren und Abholpunkte stimmen wir mit Ihnen ab.', 'labor', 150),
    'li-m25-sie-behandeln': med('gelb', 'Sie behandeln.<br>Wir fahren.', 'Der Weg ins Labor muss nicht Ihr Praxisteam beschäftigen. Wir übernehmen die Fahrt, gekühlt in ThermoSecure-Kühlboxen.', 'stetho', 124),
    'li-m26-laborproben': med('hell', 'Laborproben.', 'Proben auf dem Weg ins Labor fahren bei uns in der ThermoSecure-Kühlbox. Von der Abholung bis zur Übergabe.', 'probe', 140),
    'li-m27-anfrage-checkliste': med('schwarz', 'Vier Angaben<br>für Ihre ' + hl('Tour.', 'schwarz'), 'Damit wir Ihre Kuriertour planen können, brauchen wir:', 'liste', 112,
        extra=steps(['Abholadresse (Praxis, Klinik)', 'Ziel (Labor, Klinik)', 'Tage und Rhythmus', 'Proben oder Medikamente'], 'schwarz')),
    'li-m28-neues-labor': med('gelb', 'Neues Labor?<br>Neue Tour.', 'Ändert sich bei Ihnen ein Ziel oder ein Abholpunkt, passen wir die Tour nach Absprache an.', 'tausch', 124),
    'li-m29-fuer-kliniken': med('hell', 'Für Kliniken.', 'Proben und Medikamente bringen wir gekühlt zwischen Klinik, Praxis und Labor. In ThermoSecure-Kühlboxen.', 'klinik', 150),
    'li-m30-praxisteam': med('schwarz', 'Weniger Wege<br>für Ihr ' + hl('Team.', 'schwarz'), 'Statt dass jemand aus der Praxis Proben ins Labor bringt, fahren wir. Gekühlt und nach festem Plan.', 'stationen', 116),
    'li-m31-medikamente': med('gelb', 'Medikamente.', 'Auch Medikamente transportieren wir gekühlt in ThermoSecure-Kühlboxen, für Praxen, Labore und Kliniken.', 'pille', 124),
    'li-m32-familienbetrieb': med('hell', 'Familienbetrieb.<br>Keine Plattform.', 'Ihre Kurierfahrten organisiert Taxi Akbulut aus Tübingen: seit 1986 ein Familienbetrieb, heute in zweiter Generation.', 'haus', 112),
    'li-m33-was-gekuehlt-heisst': med('schwarz', 'Was „gekühlt“<br>bei uns ' + hl('heißt.', 'schwarz'), 'Proben und Medikamente liegen von der Abholung bis zur Übergabe in einer ThermoSecure-Kühlbox.', 'box', 116),
    'li-m34-touren-2027': med('gelb', 'Ihre Touren<br>für 2027.', 'Das neue Jahr ist ein guter Anlass, Kurierfahrten fest zu planen. Tage, Abholpunkte und Ziele stimmen wir mit Ihnen ab.', 'kalender', 124),
    'li-m35-schwaerzlocher-str': med('hell', 'Aus der<br>Schwärzlocher<br>Str. 37.', 'Unser Betrieb sitzt in Tübingen. Von hier aus fahren wir Proben und Medikamente für Praxen, Labore und Kliniken in Tübingen und Umgebung.', 'pin', 112),
    'li-m36-erst-reden': med('schwarz', 'Erst reden.<br>Dann ' + hl('fahren.', 'schwarz'), 'Konditionen, Tage und Abholpunkte besprechen wir vorab mit Ihnen. Danach steht Ihre Tour.', 'sprechen', 124),
    'li-m37-bewertungen': med('gelb', 'Über 700<br>Bewertungen.', 'Gesamtnote 4,9 von 5 auf ProvenExpert für Taxi Akbulut Tübingen. Derselbe Betrieb fährt Ihre Proben.', None, 124,
        small=RAT2 + '. Medizinischer Kurierdienst für Praxen, Labore und Kliniken.', big='4,9'),
    'li-m38-seit-1986': med('hell', 'Seit 1986<br>in Tübingen<br>unterwegs.', 'Taxi Akbulut ist ein Familienbetrieb in zweiter Generation. Seit 2026 sind es 40 Jahre.', 'lenkrad', 112),

    # ---- Chauffeurservice V-Klasse, Serie 2
    'li-v10-weihnachtsfeier': vframe('WEIHNACHTSFEIER', f'Das Team feiert.<br>Wir fahren{dot}', 'Bis zu 7 Gäste pro Fahrt in der Mercedes-Benz V-Klasse. Größere Gruppen fahren wir in mehreren Fahrten, den Preis vereinbaren wir vorab.', 'glas', 104),
    'li-v11-95-euro': vframe('FLUGHAFEN STUTTGART', f'Festpreis ab<br>Tübingen{dot}', 'Tübingen bis Flughafen Stuttgart in der V-Klasse. Eine von 15 Festpreisstrecken zu Flughäfen.', None, 100,
        foot='Endpreis inkl. MwSt. · Stand: Oktober 2026', big='95 €'),
    'li-v12-worauf-wir-achten': vframe('WORAUF WIR ACHTEN', f'Vier Dinge.<br>Jede Fahrt{dot}', '', 'liste', 108,
        extra=('<div style="display:flex;flex-direction:column;border-top:1px solid #2A2A3A;margin-top:-20px">' + ''.join(
            f'<div style="display:flex;align-items:center;gap:26px;padding:16px 0;border-bottom:1px solid #2A2A3A"><span style="font-weight:700;font-size:20px;color:{G};letter-spacing:2px;width:40px">{i + 1:02d}</span><span style="font-weight:500;font-size:32px">{t}</span></div>'
            for i, t in enumerate(['Pünktlichkeit', 'Zuverlässigkeit', 'Gepflegtes Auftreten', 'Hochwertige Fahrzeuge'])) + '</div>')),
    'li-v13-bahnhof': vframe('ABHOLUNG BAHNHOF', f'Angekommen.<br>Kurz melden{dot}', 'Sie melden sich nach der Ankunft per Telefon oder WhatsApp, Ihr Fahrer fährt am Abholpunkt vor. Diese Abholung ist kostenlos.', 'zug', 104,
        foot='Abholung mit Namensschild in der Ankunftshalle gegen Aufpreis.'),
    'li-v14-espresso': vframe('AN BORD', f'Espresso, bevor<br>es losgeht{dot}', 'Im exklusiven Chauffeurservice bereiten wir Ihren Espresso frisch im Fahrzeug zu, in der Mercedes-Benz V-Klasse.', 'tasse', 100),
    'li-v15-befreundete-fahrservices': vframe('GRÖSSERE VERANSTALTUNGEN', f'Mehr Gäste.<br>Mehr V-Klassen{dot}', 'Shuttles für Veranstaltungen fahren wir auch gemeinsam mit befreundeten Fahrservices aus der Region, etwa Fahrservice Legion und Fahrservice Hain.', 'zwei_vans', 100),
    'li-v16-ankunftsrechner': vframe('ANKUNFTSRECHNER', f'Wann losfahren?<br>Ausgerechnet{dot}', 'Der Ankunftsrechner auf taxi-akbulut.de schlägt Ihnen die passende Abfahrtszeit ab Ihrer Adresse zum Flughafen vor.', 'uhr', 100),
    'li-v17-bewertungen': vframe('BEWERTUNGEN', f'Über 700<br>Bewertungen{dot}', 'Gesamtnote 4,9 von 5 auf ProvenExpert. Google allein: 4,8.', None, 104,
        foot=RAT2, big='4,9'),
    'li-v18-gat': vframe('GENERAL AVIATION TERMINAL', f'Bis vors GAT{dot}', 'Zum General Aviation Terminal am Flughafen Stuttgart fahren wir als Mietwagen ohne Taxischild, auf Vorbestellung. Zum Festpreis wie zum Terminal.', 'flug', 112),
    'li-v19-selbst-aendern': vframe('KUNDENKONTO', f'Termin verschoben?<br>Fahrt verschieben{dot}', 'Online gebuchte Fahrten ändern oder stornieren Sie selbst im Kundenkonto auf taxi-akbulut.de.', 'handy', 92),
    'li-v20-keine-parkgebuehren': vframe('ABHOLUNG FLUGHAFEN', f'Keine Parkgebühren<br>für Ihren Fahrer{dot}', 'Sie melden sich nach der Landung, wir fahren am Abholpunkt vor. Das spart die Parkgebühren und kostet nichts extra.', 'parken', 92),
    'li-v21-seit-2006': vframe('DER INHABER FÄHRT SELBST', f'Seit 2006<br>am Steuer{dot}', 'Yasin Akbulut ist seit 2006 in der Branche und fährt bis heute selbst, im Familienbetrieb, den es seit 1986 gibt.', 'lenkrad', 108),
    'li-v22-zug-faellt-aus': vframe('LANGSTRECKE', f'Zug fällt aus.<br>Termin nicht{dot}', 'Wir fahren Sie deutschlandweit, von Tür zu Tür. Buchen und bezahlen können Sie direkt online.', 'zug', 104),
    'li-v23-hotel': vframe('GÄSTE ABHOLEN', f'Vom Hotel<br>zum Termin{dot}', 'Ihre Gäste übernachten in Tübingen, Reutlingen oder Stuttgart. Wir holen sie am Hotel ab und bringen sie zum Termin.', 'hotel', 108),
    'li-v24-neukunden-15': vframe('NEUKUNDEN', f'Die erste Fahrt<br>günstiger{dot}', 'Nach der Registrierung erhalten Sie 15 % auf Ihre erste online gebuchte Fahrt. Automatisch im Kundenkonto, ohne Code.', None, 100,
        foot='Gilt nicht im Tarifgebiet Tübingen.', big='15 %'),
    'li-v25-60-minuten': vframe('FLUGHAFEN STUTTGART', f'Verspätung<br>eingeplant{dot}', '60 Minuten Wartezeit sind im Festpreis enthalten. Ihren Flug verfolgen wir über Flightradar24.', None, 104, big='60 Min.'),
    'li-v26-reisen-2027': vframe('GESCHÄFTSREISEN 2027', f'Das neue Jahr<br>planen{dot}', 'Messen, Kundentermine, Flughafenfahrten: Buchen Sie Ihre Fahrten in der Mercedes-Benz V-Klasse online vor.', 'kalender', 100),
    'li-v27-deutschlandweit': vframe('DEUTSCHLANDWEIT', f'Termin in München?<br>Wir fahren{dot}', 'Langstrecken fahren wir zu jedem Ziel in Deutschland, ab Tübingen und von Tür zu Tür.', 'staedte', 92),
    'li-v28-zweite-generation': vframe('FAMILIENBETRIEB', f'Zweite Generation<br>am Steuer{dot}', 'Seit 1986 fahren wir in Tübingen. Heute führen zwei Brüder den Betrieb und sitzen selbst am Steuer.', 'personen', 92),
})

if __name__ == '__main__':
    for k, v in M.items():
        open(os.path.join(OUT, k + '.html'), 'w', encoding='utf-8').write(v)
    print(len(M), 'Motive geschrieben')

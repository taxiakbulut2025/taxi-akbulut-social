"""Serie 6: Premium-Chauffeurservice im Markenstil AKBULUT. Fahrservice (1080x1350)."""
import os, base64
D = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(D, 'motive'); os.makedirs(OUT, exist_ok=True)
G, W, GR = '#C9A227', '#FFFFFF', '#9CA3AF'
def img(n): return 'data:image/jpeg;base64,' + base64.b64encode(open(os.path.join(D, 'ph', n), 'rb').read()).decode()
dot = f'<span style="color:{G}">.</span>'
def mark(s=56):
    return (f'<div style="width:{s}px;height:{s}px;border-radius:4px;background:linear-gradient(135deg,#D4AC2E,#A88520);position:relative;flex-shrink:0">'
            f'<span style="position:absolute;left:{s*0.17}px;top:{s*0.08}px;font-weight:900;font-size:{s*0.72}px;color:#0B0B0B;line-height:1">A</span>'
            f'<span style="position:absolute;left:{s*0.66}px;top:{s*0.6}px;width:{s*0.17}px;height:{s*0.15}px;border-radius:50%;background:#fff"></span></div>')
def brackets():
    b = f'border-color:{G};border-style:solid;width:86px;height:86px;position:absolute'
    return (f'<div style="{b};border-width:4px 0 0 4px;left:44px;top:44px"></div>'
            f'<div style="{b};border-width:0 4px 4px 0;right:44px;bottom:44px"></div>')
def frame(inner, photo=None, pos='center', foot='', ph_h=860):
    ph = ''
    if photo:
        ph = (f'<div style="position:absolute;left:0;top:0;width:1080px;height:{ph_h}px;background:url({img(photo)}) {pos}/cover;filter:brightness(.72) contrast(1.1) saturate(.82)"></div>'
              f'<div style="position:absolute;left:0;top:0;width:1080px;height:{ph_h+2}px;background:linear-gradient(180deg,rgba(5,5,10,.9) 0%,rgba(5,5,10,.35) 14%,rgba(5,5,10,0) 28%,rgba(5,5,10,0) 52%,#07070C 100%)"></div>')
    fd = f'<div style="font-weight:400;font-size:19px;color:#6B7280;margin-bottom:22px;letter-spacing:.3px">{foot}</div>' if foot else ''
    return f'''<div style="width:1080px;height:1350px;box-sizing:border-box;position:relative;overflow:hidden;background:radial-gradient(ellipse 75% 60% at 50% 48%,#191929 0%,#0B0B13 55%,#030305 100%);color:{W};font-family:'Roboto',sans-serif;display:flex;flex-direction:column;padding:96px 104px 92px">
{ph}{brackets()}
<div style="display:flex;justify-content:space-between;align-items:center;position:relative">
<div style="display:flex;align-items:center;gap:16px">{mark(52)}<div style="font-weight:900;font-size:34px;letter-spacing:.5px">AKBULUT{dot}</div></div>
<div style="font-weight:500;font-size:17px;letter-spacing:6px;color:{G}">CHAUFFEURSERVICE</div>
</div>
<div style="flex-grow:1;display:flex;flex-direction:column;justify-content:{'flex-end' if photo else 'center'};gap:34px;position:relative">
{inner}
</div>
<div style="position:relative">{fd}
<div style="height:1px;background:linear-gradient(90deg,rgba(201,162,39,0),{G} 50%,rgba(201,162,39,0));margin-bottom:26px"></div>
<div style="display:flex;justify-content:space-between;align-items:center">
<div style="font-weight:500;font-size:17px;letter-spacing:5px;color:{GR}">TÜBINGEN · REUTLINGEN · STUTTGART</div>
<div style="display:flex;align-items:center;gap:14px"><span style="border:2px solid {G};color:{G};border-radius:999px;padding:9px 18px;font-weight:700;font-size:16px;letter-spacing:3px">ONLINE BUCHEN</span><span style="font-weight:700;font-size:24px">taxi-akbulut.de</span></div>
</div></div>
</div>'''
def label(t): return f'<div style="font-weight:500;font-size:21px;letter-spacing:7px;color:{G}">{t}</div>'
def h1(t, s=104): return f'<h1 style="margin:0;font-weight:900;font-size:{s}px;line-height:1.0;letter-spacing:-2px">{t}</h1>'
def body(t, s=33): return f'<p style="margin:0;font-weight:400;font-size:{s}px;line-height:1.42;color:#D1D5DB;max-width:840px">{t}</p>'
def gl(): return f'<div style="width:120px;height:3px;background:{G}"></div>'
def items(lst):
    r = ''.join(f'<div style="display:flex;align-items:center;gap:26px;padding:20px 0;border-bottom:1px solid #2A2A3A"><span style="font-weight:700;font-size:20px;color:{G};letter-spacing:2px;width:40px">{i+1:02d}</span><span style="font-weight:500;font-size:34px">{t}</span></div>' for i, t in enumerate(lst))
    return f'<div style="display:flex;flex-direction:column;border-top:1px solid #2A2A3A">{r}</div>'
def cards(lst):
    c = ''.join(f'<div style="flex:1;border:1px solid #3A3320;background:rgba(201,162,39,.06);border-radius:6px;padding:30px 30px 28px"><div style="font-weight:500;font-size:17px;letter-spacing:5px;color:{G};margin-bottom:14px">MERCEDES</div><div style="font-weight:900;font-size:44px;line-height:1.05;margin-bottom:12px">{a}</div><div style="font-weight:400;font-size:27px;color:#D1D5DB">{b}</div></div>' for a, b in lst)
    return f'<div style="display:flex;gap:22px">{c}</div>'
RAT = 'Gesamtnote aller Bewertungen auf ProvenExpert · Stand: Oktober 2026'
M = {
 'c01-termin-beginnt': frame(label('CHAUFFEURSERVICE') + h1(f'Ihr Termin<br>beginnt beim<br>Einsteigen{dot}', 100) + body('Mercedes E- und V-Klasse mit Fahrer für Geschäftsreisen in Tübingen, Reutlingen und Stuttgart.'), 'convoy.jpg', 'center 60%'),
 'c02-wir-warten': frame(label('PÜNKTLICHKEIT') + h1(f'Wir warten.<br>Nicht Sie{dot}', 128) + gl() + body('Für unsere Fahrten gilt eine Pünktlichkeitsgarantie. Kommen wir zu spät, erhalten Sie eine Gutschrift.', 35), foot='Bedingungen der Pünktlichkeitsgarantie auf taxi-akbulut.de'),
 'c03-erster-eindruck': frame(label('AUFTRETEN') + h1(f'Der erste<br>Eindruck<br>fährt vor{dot}', 100) + body('Gepflegte Fahrer, saubere Fahrzeuge, ruhige Fahrt. Sie kommen so an, wie Sie auftreten wollen.'), 'lineup.jpg', 'center 40%'),
 'c04-darauf-bauen': frame(label('PREMIUM CHAUFFEURSERVICE') + h1(f'Darauf können<br>Sie bauen{dot}', 100) + items(['Pünktlichkeitsgarantie', 'Preis vorab vereinbart', 'Mercedes E- und V-Klasse', 'Flug live verfolgt bei Abholung', 'Online buchen, mit Karte zahlen'])),
 'c05-arbeiten-sie': frame(label('FAHRZEIT IST ARBEITSZEIT') + h1(f'Arbeiten Sie.<br>Wir fahren{dot}', 112) + gl() + items(['Telefonate in Ruhe', 'E-Mails beantworten', 'Termin vorbereiten']) + body('Die Zeit im Fahrzeug gehört Ihnen.', 33)),
 'c06-gelandet': frame(label('ABHOLUNG FLUGHAFEN STUTTGART') + f'<div style="font-weight:300;font-size:150px;line-height:.9;letter-spacing:-4px;color:{G}">22:40</div>' + h1(f'Gelandet.<br>Ihr Fahrer wartet{dot}', 92) + body('Wir verfolgen Ihren Flug live. Auf Wunsch erwartet Sie Ihr Fahrer mit Namensschild in der Ankunftshalle.'), foot='Uhrzeit beispielhaft. Namensschild gegen Aufpreis.'),
 'c07-tuer-offen': frame(label('ZUVERLÄSSIGKEIT') + h1(f'Die Tür ist<br>schon offen{dot}', 108) + body('Ihr Fahrer ist zur vereinbarten Zeit vor Ort. Sie steigen ein, der Rest ist unsere Aufgabe.'), 'chauffeur.jpg', 'center 35%'),
 'c08-wagen-anlass': frame(label('FAHRZEUGE') + h1(f'Der Wagen<br>passt zum<br>Anlass{dot}', 108) + cards([('E-Klasse', 'Limousine oder T-Modell'), ('V-Klasse', 'bis 7 Fahrgäste')]) + body('Für die Geschäftsreise allein oder die Delegation mit Gepäck.', 30)),
 'c09-seit-1986': frame(label('ERFAHRUNG') + f'<div style="display:flex;align-items:flex-end;gap:24px"><div style="font-weight:900;font-size:280px;line-height:.78;letter-spacing:-10px;color:{G}">40</div><div style="font-weight:700;font-size:46px;line-height:1.05;padding-bottom:6px">Jahre<br>am Steuer</div></div>' + h1(f'Seit 1986<br>ein Familienbetrieb{dot}', 76) + body('Über 700 Bewertungen, Gesamtnote 4,9 von 5 auf ProvenExpert.'), foot=RAT),
 'c10-einmal-buchen': frame(label('TÜBINGEN · REUTLINGEN · STUTTGART') + h1(f'Einmal buchen.<br>Pünktlich<br>ankommen{dot}', 100) + body('Online buchen, Preis vorab vereinbart. Auf Wunsch auch deutschlandweit.'), 'street.jpg', 'center 50%'),
}
for k, v in M.items(): open(os.path.join(OUT, k + '.html'), 'w', encoding='utf-8').write(v)
print(len(M))

# Rendert LinkedIn-Motive (Archivo + Roboto) mit Playwright: python3 generator/render_li.py motive/a.html images/a.jpg [weitere Paare]
# Vorher einmalig: (cd generator && npm install) und pip install playwright
import base64, sys, os
from playwright.sync_api import sync_playwright
F=os.path.join(os.path.dirname(os.path.abspath(__file__)),"node_modules","@fontsource")
def ff(fam, file, w):
    b=base64.b64encode(open(f"{F}/{fam.lower()}/files/{file}","rb").read()).decode()
    return f"@font-face{{font-family:'{fam}';font-weight:{w};src:url(data:font/woff2;base64,{b}) format('woff2');}}"
css="".join(ff("Archivo",f"archivo-latin-{w}-normal.woff2",w) for w in (500,700,800,900))+"".join(ff("Roboto",f"roboto-latin-{w}-normal.woff2",w) for w in (400,500,700,900))
pairs=sys.argv[1:]
with sync_playwright() as p:
    br=p.chromium.launch(); pg=br.new_page(viewport={"width":1080,"height":1350})
    for i in range(0,len(pairs),2):
        src,out=pairs[i],pairs[i+1]
        pg.set_content(f"<!doctype html><html lang=de><head><meta charset=utf-8><style>{css} body{{margin:0}}</style></head><body>{open(src,encoding='utf-8').read()}</body></html>")
        pg.evaluate("document.fonts.ready")
        ov=pg.evaluate("(()=>{const r=document.body.firstElementChild;return [r.scrollHeight,r.scrollWidth]})()")
        if ov[0]>1350 or ov[1]>1080: print("UEBERLAUF",src,ov); continue
        pg.screenshot(path=out,type="jpeg",quality=90,clip={"x":0,"y":0,"width":1080,"height":1350}); print("ok",out)
    br.close()

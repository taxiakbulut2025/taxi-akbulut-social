// Rendert ein Motiv (HTML-Fragment, 1080×1350) als JPEG.
// Aufruf: node generator/render.js motive/<slug>.html images/<datei>.jpg
// Vorher einmalig: (cd generator && npm install)
const fs = require('fs');
const path = require('path');
const chromium = (m => m.default || m)(require('@sparticuz/chromium'));
const puppeteer = require('puppeteer-core');

const [, , src, out] = process.argv;
if (!src || !out) { console.error('Aufruf: node generator/render.js <motiv.html> <ausgabe.jpg>'); process.exit(1); }

const FONTS = path.join(__dirname, 'node_modules/@fontsource/archivo/files');
const font = (w) => `@font-face{font-family:'Archivo';font-weight:${w};src:url('data:font/woff2;base64,${fs.readFileSync(path.join(FONTS, `archivo-latin-${w}-normal.woff2`)).toString('base64')}') format('woff2');}`;

(async () => {
  const body = fs.readFileSync(src, 'utf8');
  if (/\{\{/.test(body)) throw new Error('Unaufgelöster Platzhalter in ' + src);
  const html = `<!doctype html><html lang="de"><head><meta charset="utf-8"><style>${[500, 700, 900].map(font).join('\n')}\nbody{margin:0}</style></head><body>${body}</body></html>`;
  const browser = await puppeteer.launch({ args: chromium.args, executablePath: await chromium.executablePath(), headless: true });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1350, deviceScaleFactor: 1 });
  await page.setContent(html, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  if (!(await page.evaluate(() => document.fonts.check('900 40px Archivo')))) throw new Error('Schrift Archivo nicht geladen');
  // Überlauf-Prüfung: Text darf nicht aus dem Bild ragen
  const overflow = await page.evaluate(() => {
    const root = document.body.firstElementChild;
    return root.scrollHeight > 1350 || root.scrollWidth > 1080;
  });
  if (overflow) throw new Error('Inhalt ragt über 1080×1350 hinaus: ' + src);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  await page.screenshot({ path: out, type: 'jpeg', quality: 90, clip: { x: 0, y: 0, width: 1080, height: 1350 } });
  await browser.close();
  console.log('ok', out);
})().catch((e) => { console.error(e.message || e); process.exit(1); });

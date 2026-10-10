// Rendert ein animiertes Reel-Motiv (1080x1920) als Einzelbilder.
// Aufruf: node generator/reel.js motive/<slug>-reel.html <frames-ordner> 9 30
const fs = require('fs');
const path = require('path');
const chromium = (m => m.default || m)(require('@sparticuz/chromium'));
const puppeteer = require('puppeteer-core');
const [, , src, outDir, secs = '9', fps = '30'] = process.argv;
const FONTS = path.join(__dirname, 'node_modules/@fontsource/archivo/files');
const font = (w) => `@font-face{font-family:'Archivo';font-weight:${w};src:url('data:font/woff2;base64,${fs.readFileSync(path.join(FONTS, `archivo-latin-${w}-normal.woff2`)).toString('base64')}') format('woff2');}`;
(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const html = `<!doctype html><html lang="de"><head><meta charset="utf-8"><style>${[500, 700, 900].map(font).join('\n')}\nbody{margin:0}</style></head><body>${fs.readFileSync(src, 'utf8')}</body></html>`;
  const browser = await puppeteer.launch({ args: chromium.args, executablePath: await chromium.executablePath(), headless: true });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await page.setContent(html, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => document.getAnimations().forEach((a) => a.pause()));
  const n = Math.round(+secs * +fps);
  for (let i = 0; i < n; i++) {
    const t = (i / +fps) * 1000;
    await page.evaluate((t) => document.getAnimations().forEach((a) => { a.currentTime = t; }), t);
    await page.screenshot({ path: path.join(outDir, `f${String(i).padStart(4, '0')}.jpg`), type: 'jpeg', quality: 92 });
  }
  await browser.close();
  console.log('frames', n);
})().catch((e) => { console.error(e); process.exit(1); });

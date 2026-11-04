// Full product walkthrough of the Capture IV project viewer (demo project "Riverside Commons").
const { chromium } = require('playwright');
const fs = require('fs');
const S = process.env.S, OUT = process.env.OUT;
const W = 1600, H = 900;
const cursorScript = fs.readFileSync(S + '/record.js', 'utf8').match(/const cursorScript = `([\s\S]*?)`;/)[1];

(async () => {
  fs.rmSync(OUT, { recursive: true, force: true }); fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ viewport: { width: W, height: H } });
  await ctx.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: 'http://127.0.0.1:5009' });
  await ctx.route(/unpkg\.com\//, r => { const m = r.request().url().match(/unpkg\.com\/([^@]+)@[^/]+\/(.*)$/);
    const f = S + '/cdn/node_modules/' + m[1] + '/' + m[2].split('?')[0];
    return fs.existsSync(f) ? r.fulfill({ path: f, contentType: f.endsWith('.css') ? 'text/css' : 'application/javascript' }) : r.abort(); });
  await ctx.route(/(tile\.openstreetmap|arcgisonline|fonts\.g)/, r => r.abort());
  await ctx.addInitScript(cursorScript);
  const p = await ctx.newPage();
  await p.goto('http://127.0.0.1:5009/'); await p.fill('input[name=code]', 'RVCM');
  await p.locator('form button').first().click(); await p.waitForLoadState('networkidle');
  const base = p.url().split('?')[0];
  await p.goto(base + '?tab=map&date=2026-11-02'); await p.waitForLoadState('networkidle'); await p.waitForTimeout(1200);

  const cdp = await ctx.newCDPSession(p); const frames = []; let n = 0;
  cdp.on('Page.screencastFrame', async f => { const file = `${OUT}/f${String(n++).padStart(5, '0')}.jpg`;
    fs.writeFileSync(file, Buffer.from(f.data, 'base64')); frames.push({ file, t: f.metadata.timestamp });
    try { await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }); } catch {} });
  const cast = () => cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: W, maxHeight: H, everyNthFrame: 1 }).catch(() => {});
  await cast();
  const markers = []; const mark = name => markers.push({ name, t: Date.now() / 1000 });
  const tick = setInterval(() => p.evaluate(() => document.documentElement.style.setProperty('--tick', Math.random())).catch(() => {}), 33);
  const centre = async loc => { const bx = await loc.boundingBox(); return [bx.x + bx.width / 2, bx.y + bx.height / 2]; };
  const glide = (x, y, steps = 28) => p.mouse.move(x, y, { steps });
  const click = async () => { await p.mouse.down(); await p.waitForTimeout(80); await p.mouse.up(); };
  const ripple = (x, y) => p.evaluate(([x, y]) => document.dispatchEvent(new MouseEvent('mousedown', { clientX: x, clientY: y, bubbles: true })), [x, y]);
  const nav = async url => { await p.goto(url, { waitUntil: 'domcontentloaded' }); await cast(); await p.waitForLoadState('networkidle').catch(() => {}); };
  let x, y;

  mark('start'); await p.mouse.move(900, 520); await p.waitForTimeout(1300);

  // 1. Select a date from the calendar
  mark('date');
  [x, y] = await centre(p.locator('#flight-dates-toggle')); await glide(x, y); await p.waitForTimeout(250); await click(); await p.waitForTimeout(900);
  const day = p.locator('.calendar-day:not(:disabled)', { hasText: /^28$/ });
  if (!(await day.count())) { [x, y] = await centre(p.locator('#calendar-prev')); await glide(x, y, 18); await click(); await p.waitForTimeout(600); }
  [x, y] = await centre(day.first()); await glide(x, y); await p.waitForTimeout(400);
  await ripple(x, y); await p.waitForTimeout(200); mark('date-nav');
  await nav(base + '?tab=map&date=2026-10-28'); await p.waitForTimeout(1100);

  // 2. Hit a flight route -> popup -> linked flight video
  mark('route');
  const label = p.locator('.viewer-route-start', { hasText: 'Podium deck orbit' });
  [x, y] = await centre(label); await glide(x, y, 34); await p.waitForTimeout(300); await click(); await p.waitForTimeout(1300);
  const link = p.locator('.viewer-route-popup-link').first(); const href = await link.getAttribute('href');
  [x, y] = await centre(link); await glide(x, y, 22); await p.waitForTimeout(350); await ripple(x, y); await p.waitForTimeout(200); mark('video-nav');
  await nav(href); await p.waitForSelector('#flight-detail-dialog:not([hidden]) video'); mark('video');
  const vid = p.locator('#flight-detail-dialog video');
  await vid.evaluate(v => new Promise(r => { if (v.readyState >= 2) return r(); v.addEventListener('loadeddata', r, { once: true }); setTimeout(r, 5000); }));
  [x, y] = await centre(vid); await glide(x, y, 26); await p.waitForTimeout(200); await click();
  await vid.evaluate(v => { v.muted = true; return v.play(); }); await p.mouse.move(x + 300, y + 230, { steps: 24 }); await p.waitForTimeout(3600);
  [x, y] = await centre(p.locator('.flight-detail-close')); await glide(x, y, 24); await p.waitForTimeout(200); await click(); await p.waitForTimeout(800);

  // 3. Flight library -> another flight
  mark('library');
  [x, y] = await centre(p.locator('#flight-library-toggle')); await glide(x, y, 30); await p.waitForTimeout(200); await click(); await p.waitForTimeout(1100);
  const card = p.locator('.film-card', { hasText: 'North façade pass' }).first(); const cardHref = await card.getAttribute('href');
  [x, y] = await centre(card); await glide(x, y, 26); await p.waitForTimeout(400); await ripple(x, y); await p.waitForTimeout(200); mark('lib-nav');
  await nav(new URL(cardHref, base).href); await p.waitForSelector('#flight-detail-dialog:not([hidden]) video'); mark('lib-video');
  await p.locator('#flight-detail-dialog video').evaluate(v => { v.muted = true; return v.play(); }); await p.waitForTimeout(2600);
  [x, y] = await centre(p.locator('.flight-detail-close')); await glide(x, y, 24); await p.waitForTimeout(200); await click(); await p.waitForTimeout(700);

  // 4. Compare
  mark('compare');
  [x, y] = await centre(p.locator('#compare-toggle')); await glide(x, y, 30); await p.waitForTimeout(250); await click(); await p.waitForTimeout(1600);
  [x, y] = await centre(p.locator('#compare-divider')); await glide(x, y, 26); await p.waitForTimeout(250);
  await p.mouse.down(); await p.mouse.move(x - 260, y, { steps: 40 }); await p.waitForTimeout(250); await p.mouse.move(x + 220, y, { steps: 50 }); await p.waitForTimeout(250); await p.mouse.move(x, y, { steps: 30 }); await p.mouse.up();
  await p.waitForTimeout(900);
  [x, y] = await centre(p.locator('#compare-close')); await glide(x, y, 26); await p.waitForTimeout(200); await click(); await p.waitForTimeout(900);

  // 4b. Documents: open the tab, browse, search, download
  mark('docs');
  const docsTab = p.locator('.viewer-topnav-tabs a', { hasText: 'Documents' }); const docsHref = await docsTab.getAttribute('href');
  [x, y] = await centre(docsTab); await glide(x, y, 34); await p.waitForTimeout(300); await ripple(x, y); await p.waitForTimeout(200); mark('docs-nav');
  await nav(new URL(docsHref, base).href); await p.waitForTimeout(700); mark('docs-list');
  const rows = p.locator('.viewer-docs .document-row');
  for (let i = 0; i < Math.min(4, await rows.count()); i++) { [x, y] = await centre(rows.nth(i)); await glide(x - 160, y, 16); await p.waitForTimeout(260); }
  [x, y] = await centre(p.locator('#viewer-search')); await glide(x, y, 26); await p.waitForTimeout(200); await click(); mark('docs-search');
  await p.keyboard.type('pour', { delay: 140 }); await p.waitForTimeout(900); mark('docs-filtered');
  const dl = p.locator('.viewer-docs .document-row:not([hidden]) a').first();
  [x, y] = await centre(dl); await glide(x, y, 30); await p.waitForTimeout(350); await ripple(x, y); mark('docs-dl'); await p.waitForTimeout(900);
  await p.locator('#viewer-search').fill(''); await p.locator('#viewer-search').dispatchEvent('input'); await p.waitForTimeout(300);

  // 5. Share
  mark('share');
  [x, y] = await centre(p.locator('#share-button')); await glide(x, y, 30); await p.waitForTimeout(250); await click(); await p.waitForTimeout(1100);
  [x, y] = await centre(p.locator('[data-copy=share-code]')); await glide(x, y, 26); await p.waitForTimeout(250); await click(); await p.waitForTimeout(1600);
  mark('end');

  clearInterval(tick); await cdp.send('Page.stopScreencast').catch(() => {}); await p.waitForTimeout(200);
  fs.writeFileSync(`${OUT}/frames.json`, JSON.stringify({ frames, markers }, null, 1));
  console.log('frames', frames.length, markers.map(m => m.name).join(','));
  await b.close();
})();

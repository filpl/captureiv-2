// Records a scripted product tour of the Capture IV project viewer as
// timestamped JPEG frames (CDP screencast) plus a marker log for post-production.
const { chromium } = require('playwright');
const fs = require('fs');
const S = process.env.S, OUT = process.env.OUT;
const W = 1600, H = 900;

const cursorScript = `
(() => {
  const install = () => {
    if (document.getElementById('__demo_cursor')) return;
    const c = document.createElement('div');
    c.id = '__demo_cursor';
    c.innerHTML = '<svg width="26" height="30" viewBox="0 0 26 30"><path d="M3 2 L3 24 L9 18.5 L13 27.5 L17 25.8 L13 17 L21 17 Z" fill="#0b1530" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, {position:'fixed', zIndex:2147483647, left:'0', top:'0', pointerEvents:'none',
      filter:'drop-shadow(0 4px 8px rgba(11,21,48,.35))', transform:'translate(-3px,-2px)', transition:'none'});
    const r = document.createElement('div');
    r.id = '__demo_ripple';
    Object.assign(r.style, {position:'fixed', zIndex:2147483646, width:'44px', height:'44px', marginLeft:'-22px', marginTop:'-22px',
      borderRadius:'50%', border:'2px solid rgba(37,99,235,.9)', background:'rgba(37,99,235,.18)', pointerEvents:'none', opacity:'0',
      transform:'scale(.3)', transition:'transform .45s cubic-bezier(.2,.7,.2,1), opacity .45s ease'});
    document.documentElement.append(r, c);
    const pos = JSON.parse(sessionStorage.getItem('__cur') || '{"x":800,"y":450}');
    c.style.left = pos.x + 'px'; c.style.top = pos.y + 'px';
    addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px';
      sessionStorage.setItem('__cur', JSON.stringify({x:e.clientX, y:e.clientY})); }, true);
    addEventListener('mousedown', e => { r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px';
      r.style.transition = 'none'; r.style.opacity = '1'; r.style.transform = 'scale(.3)';
      requestAnimationFrame(() => { r.style.transition = 'transform .45s cubic-bezier(.2,.7,.2,1), opacity .5s ease';
        r.style.transform = 'scale(1)'; r.style.opacity = '0'; }); }, true);
    // hide scrollbars for a clean capture
    const st = document.createElement('style'); st.textContent = '::-webkit-scrollbar{display:none}'; document.documentElement.append(st);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install); else install();
})();`;

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  await ctx.route(/unpkg\.com\//, r => { const m = r.request().url().match(/unpkg\.com\/([^@]+)@[^/]+\/(.*)$/);
    const f = S + '/cdn/node_modules/' + m[1] + '/' + m[2].split('?')[0];
    return fs.existsSync(f) ? r.fulfill({ path: f, contentType: f.endsWith('.css') ? 'text/css' : 'application/javascript' }) : r.abort(); });
  await ctx.route(/(tile\.openstreetmap|arcgisonline|fonts\.g)/, r => r.abort());
  await ctx.addInitScript(cursorScript);
  const p = await ctx.newPage();

  // sign in to the viewer with the project code (before recording)
  await p.goto('http://127.0.0.1:5009/'); await p.fill('input[name=code]', 'RVCM');
  await p.locator('form button').first().click(); await p.waitForLoadState('networkidle');
  const base = p.url().split('?')[0];
  await p.goto(base + '?tab=map&date=2026-10-28'); await p.waitForLoadState('networkidle'); await p.waitForTimeout(1500);

  // ---- start capture
  const cdp = await ctx.newCDPSession(p);
  const frames = []; let n = 0; const t0 = Date.now();
  cdp.on('Page.screencastFrame', async f => {
    const file = `${OUT}/f${String(n++).padStart(5, '0')}.jpg`;
    fs.writeFileSync(file, Buffer.from(f.data, 'base64'));
    frames.push({ file, t: f.metadata.timestamp });
    try { await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }); } catch {}
  });
  const startCast = () => cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: W, maxHeight: H, everyNthFrame: 1 });
  await startCast();
  const markers = []; const mark = name => markers.push({ name, t: Date.now() / 1000 });
  // keep frames flowing even when nothing repaints
  const tick = setInterval(() => p.evaluate(() => { document.documentElement.style.setProperty('--tick', Math.random()); }).catch(() => {}), 33);

  const vid0 = async () => { await p.locator('#flight-detail-dialog video').evaluate(v => new Promise(r => { if (v.readyState >= 2) return r(); v.addEventListener('loadeddata', r, { once: true }); setTimeout(r, 5000); })); };
  const glide = async (x, y, steps = 45) => { await p.mouse.move(x, y, { steps }); };
  const ripple = async (x, y) => { await p.evaluate(([x, y]) => document.dispatchEvent(new MouseEvent('mousedown', { clientX: x, clientY: y, bubbles: true })), [x, y]); };
  const press = async () => { await p.mouse.down(); await p.waitForTimeout(90); await p.mouse.up(); };
  const centre = async loc => { const bx = await loc.boundingBox(); return [bx.x + bx.width / 2, bx.y + bx.height / 2]; };

  mark('map'); await p.mouse.move(820, 640); await p.waitForTimeout(1800);

  // 1. select a route
  mark('route');
  const label = p.locator('.viewer-route-start', { hasText: 'Podium deck orbit' });
  let [x, y] = await centre(label); await glide(x, y, 60); await p.waitForTimeout(500);
  await p.mouse.down(); await p.waitForTimeout(90); await p.mouse.up();
  await p.waitForTimeout(1800);

  // 2. open the linked flight
  mark('video');
  const link = p.locator('.viewer-route-popup-link').first();
  await p.waitForTimeout(500);
  const href = await link.getAttribute('href');
  [x, y] = await centre(link); console.log('link at', Math.round(x), Math.round(y));
  await glide(x, y, 40); await p.waitForTimeout(400);
  await ripple(x, y); await p.waitForTimeout(250); mark('nav');
  await p.goto(href, { waitUntil: 'domcontentloaded' });
  await startCast().catch(() => {});
  await p.waitForSelector('#flight-detail-dialog:not([hidden]) video'); mark('dialog'); await vid0(); await p.waitForTimeout(700);
  const vid = p.locator('#flight-detail-dialog video');
  [x, y] = await centre(vid); await glide(x, y, 40); await p.waitForTimeout(300);
  await press(); mark('play');
  await vid.evaluate(v => { v.muted = true; return v.play(); });
  await p.mouse.move(x + 260, y + 210, { steps: 50 });
  await p.waitForTimeout(5200);

  // 3. close and open documents
  mark('close');
  const close = p.locator('.flight-detail-close');
  [x, y] = await centre(close); await glide(x, y, 45); await p.waitForTimeout(300); await press();
  await p.waitForTimeout(900);
  const docsTab = p.locator('.viewer-topnav-tabs a', { hasText: 'Documents' });
  const docsHref = await docsTab.getAttribute('href');
  [x, y] = await centre(docsTab); await glide(x, y, 55); await p.waitForTimeout(350);
  await ripple(x, y); await p.waitForTimeout(250);
  mark('docsnav');
  await p.goto(new URL(docsHref, p.url()).href, { waitUntil: 'domcontentloaded' }); mark('docs');
  await startCast().catch(() => {});
  await p.waitForTimeout(900);
  const rows = p.locator('.viewer-docs .document-row');
  for (let i = 0; i < Math.min(3, await rows.count()); i++) { [x, y] = await centre(rows.nth(i)); await glide(x - 120, y, 30); await p.waitForTimeout(500); }
  const dl = rows.nth(0).locator('a');
  [x, y] = await centre(dl); await glide(x, y, 40); await p.waitForTimeout(2200);
  mark('end');

  clearInterval(tick);
  await cdp.send('Page.stopScreencast').catch(() => {});
  await p.waitForTimeout(300);
  fs.writeFileSync(`${OUT}/frames.json`, JSON.stringify({ frames, markers }, null, 1));
  console.log('frames', frames.length, 'seconds', (Date.now() - t0) / 1000, 'markers', markers.map(m => m.name).join(','));
  await b.close();
})();

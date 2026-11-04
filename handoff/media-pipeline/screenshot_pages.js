const { chromium } = require('playwright'); const fs=require('fs'); const S=process.env.S; const css=fs.readFileSync(S+'/darkmix/dark-mix.css','utf8');
const OPT = JSON.parse(process.env.OPT);  // {name:{dark:[selectors], extra:"css"}}
(async()=>{const b=await chromium.launch();
for (const [name,o] of Object.entries(OPT)){
 const p=await b.newPage({viewport:{width:1440,height:900}});
 await p.goto('http://127.0.0.1:5173'+(o.path||'/')); await p.addStyleTag({content:css+(o.extra||'')+'.motion-reveal,.motion-reveal *{opacity:1!important;transform:none!important;filter:none!important;transition:none!important}'});
 await p.evaluate(()=>document.querySelectorAll('img').forEach(i=>i.loading='eager'));
 await p.evaluate(sel=>sel.forEach(s=>document.querySelectorAll(s).forEach(e=>e.classList.add('dk'))), o.dark);
 if(o.nav) await p.evaluate(()=>document.querySelector('.nav').classList.add('dk-nav'));await p.addStyleTag({content:'.nav *{transition:none!important}'});
 await p.evaluate(()=>document.querySelectorAll('video').forEach(v=>{v.pause();v.currentTime=3.5}));
 // reveal-on-scroll content
 await p.evaluate(async()=>{for(let y=0;y<document.body.scrollHeight;y+=600){scrollTo(0,y);await new Promise(r=>setTimeout(r,60))}scrollTo(0,0)});
 await p.evaluate(()=>document.querySelectorAll('.reveal,[data-reveal]').forEach(e=>e.classList.add('is-visible','visible','in')));
 await p.evaluate(()=>Promise.all([...document.images].map(i=>i.complete?0:new Promise(r=>{i.onload=i.onerror=r;setTimeout(r,4000)}))));await p.waitForTimeout(700);
 await p.screenshot({path:`${S}/darkmix/${name}.png`,fullPage:true}); await p.close();}
await b.close();})();

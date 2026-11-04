// Deterministic phone scroll-through: eased scroll positions, one screenshot per 30fps frame, at 2x pixel density
const { chromium, devices } = require('playwright'); const fs=require('fs'); const S=process.env.S, OUT=S+'/mobile/rec2';
(async()=>{fs.rmSync(OUT,{recursive:true,force:true});fs.mkdirSync(OUT,{recursive:true});
const b=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});
const ctx=await b.newContext({...devices['iPhone 13'],deviceScaleFactor:2});const p=await ctx.newPage();
let n=0; const shot=async()=>{await p.screenshot({path:`${OUT}/f${String(n++).padStart(5,'0')}.jpg`,type:'jpeg',quality:85});};
const hold=async s=>{for(let i=0;i<Math.round(s*30);i++){await shot();await p.waitForTimeout(8);}};
const scroll=async(to,s)=>{const y0=await p.evaluate(()=>scrollY);const m=Math.round(s*30);for(let i=1;i<=m;i++){const k=i/m,e=k<.5?4*k**3:1-(-2*k+2)**3/2;await p.evaluate(y=>scrollTo(0,y),y0+(to-y0)*e);await p.waitForTimeout(12);await shot();}};
const top=sel=>p.evaluate(s=>{const e=document.querySelector(s);return e?Math.max(0,e.getBoundingClientRect().top+scrollY-64):null},sel);
const visit=async(path,stops)=>{await p.goto('http://127.0.0.1:5173'+path,{waitUntil:'networkidle'});
 await p.addStyleTag({content:'html{scroll-behavior:auto!important}'});await p.waitForTimeout(400);await hold(1.3);
 for(const [sel,h] of stops){const y=await top(sel);if(y==null)continue;await scroll(y,1.1);await hold(h);}
 const end=await p.evaluate(()=>document.documentElement.scrollHeight-innerHeight);await scroll(end,1.2);await hold(.9);};
await visit('/',[['.product-tour',3.2],['.research-notes',1.0],['.software-story',1.0],['.feature-showcase',1.2],['.how-it-works',1.2],['.how-step:nth-child(2)',1.0],['.how-step:nth-child(3)',1.0],['.product-quotes',.8]]);
await scroll(0,1.0);await hold(.3);await p.click('.menu');await p.waitForTimeout(300);await hold(1.4);
await visit('/solutions',[['.core-features',1.2],['.phases',1.0],['.methods',1.0],['.viewer-demo-section',1.4]]);
await visit('/pricing',[['.package-section',1.2],['.quote-request',1.2]]);
console.log('frames',n);await b.close();})();

// Desktop scroll-through of every public page: eased scrolls, one screenshot per 30fps frame
const { chromium } = require('playwright'); const fs=require('fs'); const S=process.env.S, OUT=S+'/desktop/rec';
(async()=>{fs.rmSync(OUT,{recursive:true,force:true});fs.mkdirSync(OUT,{recursive:true});
const b=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});
const p=await b.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
let n=0; const shot=async()=>{await p.screenshot({path:`${OUT}/f${String(n++).padStart(5,'0')}.jpg`,type:'jpeg',quality:88});};
const hold=async s=>{for(let i=0;i<Math.round(s*30);i++){await shot();await p.waitForTimeout(6);}};
const scroll=async(to,s)=>{const y0=await p.evaluate(()=>scrollY);const m=Math.round(s*30);for(let i=1;i<=m;i++){const k=i/m,e=k<.5?4*k**3:1-(-2*k+2)**3/2;await p.evaluate(y=>scrollTo(0,y),y0+(to-y0)*e);await p.waitForTimeout(10);await shot();}};
const top=sel=>p.evaluate(s=>{const e=document.querySelector(s);return e?Math.max(0,e.getBoundingClientRect().top+scrollY-80):null},sel);
const visit=async(path,stops)=>{await p.goto('http://127.0.0.1:5173'+path,{waitUntil:'networkidle'});
 await p.addStyleTag({content:'html{scroll-behavior:auto!important}'});await p.waitForTimeout(500);await hold(1.6);
 for(const [sel,h] of stops){const y=await top(sel);if(y==null)continue;await scroll(y,1.2);await hold(h);}
 const end=await p.evaluate(()=>document.documentElement.scrollHeight-innerHeight);await scroll(end,1.3);await hold(.8);};
await visit('/',[['.product-tour',4.0],['.research-notes',1.2],['.software-story',1.2],['.feature-showcase',1.2],['.how-it-works',1.2],['.how-step:nth-child(2)',1.0],['.how-step:nth-child(3)',1.0],['.product-quotes',.9]]);
await visit('/platform',[['.platform-viewer-showcase',2.2],['.compact-section',1.2],['.compact-section:nth-of-type(4)',1.0]]);
await visit('/solutions',[['.core-features',1.4],['.phases',1.2],['.methods',1.2],['.insights',1.0],['.viewer-demo-section',1.6]]);
await visit('/pricing',[['.package-section',1.4],['.quote-request',1.4]]);
await visit('/clients',[['.compact-section',1.4]]);
await visit('/about',[['.compact-section',1.4]]);
await visit('/contact',[]);
console.log('frames',n);await b.close();})();

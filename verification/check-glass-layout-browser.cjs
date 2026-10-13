'use strict';
const {chromium}=require(process.env.KOTOBA_PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const routes=['/','/explore','/kanji','/kanji/1','/kanji/160','/kanji/practice','/radicals','/radicals/r001','/hiragana','/katakana','/jlpt','/jlpt/N5','/jlpt/N1','/jlpt/N5/practice','/jlpt/N5/exam-practice','/jlpt/N5/mock','/everyday','/verbs','/grammar','/grammar/g-001','/roadmap','/roadmap/smartphones-apps','/speaking','/review','/flashcards','/writing-practice','/write','/japan','/dashboard','/streak','/practice','/games','/favorites','/mistakes','/backup','/sync','/privacy','/about','/feedback','/data-controls','/kanji-notification','/placement','/stories','/stories/neko-to-ame','/conversations','/conversations/self-introduction','/search?q=sor'];
const critical=['/','/kanji/1','/radicals/r001','/everyday','/verbs','/jlpt/N5','/jlpt/N5/mock','/speaking','/review','/japan','/kanji-notification','/backup'];
async function audit(page){return page.evaluate(()=>{
const overflow=[],offBlur=[];const root=document.documentElement;
for(const element of document.querySelectorAll('main *,.site-header *')){
 const r=element.getBoundingClientRect(),s=getComputedStyle(element);
 if(!r.width||!r.height||element.closest('svg,.journey-art,.koto-mascot,.japan-map-wrap,.kotoba-intro')||['absolute','fixed'].includes(s.position))continue;
 if(element.clientWidth>0&&element.scrollWidth>element.clientWidth+3&&!['auto','scroll','hidden','clip'].includes(s.overflowX))overflow.push({class:element.className,tag:element.tagName,width:element.clientWidth,content:element.scrollWidth,text:element.textContent.slice(0,50)});
}
// Inspect real text line boxes, including text hidden by a too-narrow card.
const walk=document.createTreeWalker(document.querySelector('main'),NodeFilter.SHOW_TEXT);
let text;
while(text=walk.nextNode()){
 if(!text.textContent.trim())continue;const parent=text.parentElement;if(!parent||parent.closest('svg,script,style,.journey-art,.koto-mascot,.tap-effect-ripple'))continue;
 let card=parent;
 while(card&&card.tagName!=='MAIN'){
  const style=getComputedStyle(card);
  if(style.backgroundColor!=='rgba(0, 0, 0, 0)'&&style.backgroundColor!=='transparent')break;
  card=card.parentElement;
 }
 if(!card||card.tagName==='MAIN'||!card.getClientRects().length)continue;
 const bounds=card.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(text);
 for(const line of range.getClientRects())if(line.width>0&&(line.left<bounds.left-3||line.right>bounds.right+3))overflow.push({class:card.className,tag:'TEXT',text:text.textContent.trim().slice(0,50),left:line.left,right:line.right,card:[bounds.left,bounds.right]});
}
if(root.dataset.glass==='off')for(const element of document.querySelectorAll('body *')){
 const s=getComputedStyle(element);if(element.getClientRects().length&&s.backdropFilter!=='none')offBlur.push({class:element.className,filter:s.backdropFilter});
}
return {overflow:overflow.slice(0,12),offBlur,documentWidth:root.scrollWidth,viewport:innerWidth};
});}
(async()=>{
const browser=await chromium.launch({executablePath:process.env.KOTOBA_CHROME,args:['--no-sandbox','--disable-dev-shm-usage']});
const results=[],failures=[],errors=[];
for(const width of [320,390,1180])for(const theme of ['sakura-journey','kyoto-night'])for(const glass of ['on','off']){
 const page=await browser.newPage({viewport:{width,height:844}});
 await page.addInitScript(({theme,glass})=>{localStorage.setItem('kotoba:theme',theme);if(!localStorage.getItem('kotoba:liquid-glass'))localStorage.setItem('kotoba:liquid-glass',glass);localStorage.setItem('kotoba:onboarding:v3','1');window.KotobaStartupNative={introElapsedMs:()=>3000};},{theme,glass});
 page.on('pageerror',e=>errors.push(e.message));
 for(const route of (process.env.KOTOBA_GLASS_QUICK?['/radicals/r001','/roadmap/smartphones-apps','/japan','/kanji/1']:routes)){
  const response=await page.goto('http://127.0.0.1:5059'+route);await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(280);
  const status=response.status();if(status===404){failures.push({route,status});continue;}
  assert.equal(status,200,route);const d=await audit(page);
  if(d.overflow.length||d.offBlur.length||d.documentWidth>d.viewport+1){const f={route,width,theme,glass,...d};failures.push(f);if(failures.length<7)console.log('ISSUE',JSON.stringify(f));}
  results.push({route,width,theme,glass,largeText:false,pass:!d.overflow.length&&!d.offBlur.length&&d.documentWidth<=d.viewport+1});
 }
 if(width<600)for(const route of (process.env.KOTOBA_GLASS_QUICK?['/radicals/r001','/japan','/kanji/1']:critical)){
  await page.goto('http://127.0.0.1:5059'+route);await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(280);
  await page.addStyleTag({content:'html{font-size:200% !important} main :is(p,dd,dt,li,label,button,small){line-height:1.65}'});
  const d=await audit(page);if(d.overflow.length||d.offBlur.length||d.documentWidth>d.viewport+1)failures.push({route,width,theme,glass,largeText:true,...d});
  results.push({route,width,theme,glass,largeText:true,pass:!d.overflow.length&&!d.offBlur.length&&d.documentWidth<=d.viewport+1});
 }
 await page.goto('http://127.0.0.1:5059/kanji/1');await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(280);await page.locator('#settings-btn').click();
 const toggle=page.locator('#liquid-glass-switch');await toggle.scrollIntoViewIfNeeded();await toggle.click();const next=glass==='on'?'off':'on';assert.equal(await page.locator('html').getAttribute('data-glass'),next);assert.equal(await toggle.getAttribute('aria-checked'),String(next==='on'));
 await page.reload();assert.equal(await page.locator('html').getAttribute('data-glass'),next);assert.equal(await page.evaluate(()=>localStorage.getItem('kotoba:liquid-glass')),next);
 await page.close();console.log('Checked',width,theme,glass);
}
fs.writeFileSync(path.join(__dirname,'glass-layout-results.json'),JSON.stringify({quick:!!process.env.KOTOBA_GLASS_QUICK,layouts:results,failures,errors,scope:'Desktop Chromium, including both glass states, stored toggle and enlarged CSS text. Android WebView/device QA pending.'},null,2));
console.log('Layouts',results.length,'failures',failures.length,'JS errors',errors.length);if(failures.length)console.log('First failing screen:',JSON.stringify(failures[0]));assert.equal(failures.length,0,'See glass-layout-results.json for overflow details');assert.deepEqual(errors,[]);await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

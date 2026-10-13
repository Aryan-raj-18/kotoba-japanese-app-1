'use strict';
const {chromium}=require(process.env.KOTOBA_PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict'),fs=require('fs'),path=require('path');
async function inspect(page){
const problems=await page.evaluate(()=>{
 const out=[];for(const e of document.querySelectorAll('.modal-card *,.japan-drawer.open *,.review-card *,.speaking-card *,.flash-face,#mock-run *')){
 const r=e.getBoundingClientRect(),s=getComputedStyle(e);if(!r.width||!r.height||e.closest('svg,.tap-effect-ripple')||['fixed','absolute'].includes(s.position))continue;
 if(e.clientWidth&&e.scrollWidth>e.clientWidth+4&&!['auto','scroll','hidden','clip'].includes(s.overflowX))out.push({class:e.className,width:e.clientWidth,content:e.scrollWidth,text:e.textContent.slice(0,60)});
 }
 if(document.documentElement.dataset.glass==='off')for(const e of document.querySelectorAll('body *'))if(e.getClientRects().length&&getComputedStyle(e).backdropFilter!=='none')out.push({class:e.className,blur:getComputedStyle(e).backdropFilter});
 return out;
});assert.deepEqual(problems,[]);
const contrasts=await page.evaluate(()=>{
 const rgb=c=>c.match(/[\d.]+/g).slice(0,3).map(Number);
 const luminance=c=>rgb(c).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((n,v,i)=>n+v*[.2126,.7152,.0722][i],0);
 return [...document.querySelectorAll('.btn-primary')].filter(e=>e.getClientRects().length).map(e=>{const s=getComputedStyle(e),a=luminance(s.color),b=luminance(s.backgroundColor);return {text:e.textContent.slice(0,30),ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)}});
});for(const c of contrasts)assert(c.ratio>=4.5,JSON.stringify(c));}
(async()=>{
const browser=await chromium.launch({executablePath:process.env.KOTOBA_CHROME,args:['--no-sandbox','--disable-dev-shm-usage']});let checks=0;const errors=[];
for(const glass of ['on','off']){
 const p=await browser.newPage({viewport:{width:320,height:844}});p.on('pageerror',e=>errors.push(e.message));
 await p.addInitScript(glass=>{localStorage.setItem('kotoba:onboarding:v3','1');localStorage.setItem('kotoba:theme',glass==='on'?'sakura-journey':'kyoto-night');if(!localStorage.getItem('kotoba:liquid-glass'))localStorage.setItem('kotoba:liquid-glass',glass);window.KotobaStartupNative={introElapsedMs:()=>3000,skipIntro(){window.introSkipped=true;}};window.KotobaSpeechNative={speak(){},stop(){}};},glass);
 async function go(route){await p.goto('http://127.0.0.1:5059'+route);await p.evaluate(()=>document.fonts.ready);}
 await go('/jlpt/N5');await p.locator('[data-kanji]').first().click();await p.locator('#kanji-modal').waitFor({state:'visible'});await inspect(p);checks++;
 await go('/everyday');await p.locator('.everyday-row').first().click();await p.locator('#word-modal').waitFor({state:'visible'});await inspect(p);checks++;
 await go('/verbs');await p.locator('.verb-row').first().click();await p.locator('#verb-modal').waitFor({state:'visible'});await inspect(p);checks++;
 await go('/speaking');await p.locator('#speaking-start').click();await p.locator('#speaking-run').waitFor({state:'visible'});await inspect(p);checks++;
 await go('/review');await p.locator('#review-start').click();await p.locator('#review-run').waitFor({state:'visible'});await inspect(p);checks++;
 await go('/flashcards');await p.locator('#fc-start').click();await p.locator('.flash-face:visible').first().waitFor();await inspect(p);checks++;
 await go('/jlpt/N5/mock');await p.locator('#mock-start').click();await p.locator('#mock-options button').first().waitFor();const options=p.locator('#mock-options button');await options.nth(0).click();assert(await options.nth(0).evaluate(e=>e.classList.contains('selected')));await options.nth(1).click();assert(await options.nth(1).evaluate(e=>e.classList.contains('selected')));assert(!(await options.nth(0).evaluate(e=>e.classList.contains('selected'))));await inspect(p);checks++;
 await go('/japan');await p.locator('.japan-place-card').filter({hasText:'Tokyo'}).first().click();await p.locator('.japan-drawer.open').waitFor();await inspect(p);checks++;
 await go('/kanji/1');await p.locator('#settings-btn').click();const t=p.getByRole('switch',{name:'Liquid Glass',exact:true});await t.scrollIntoViewIfNeeded();await t.press('Space');assert.equal(await t.getAttribute('aria-checked'),String(glass==='off'));await t.press('Enter');assert.equal(await t.getAttribute('aria-checked'),String(glass==='on'));checks++;
 // The pre-Python native opening document uses the same origin and preference.
 const intro=fs.readFileSync(path.join(__dirname,'../android/app/src/main/assets/kotoba-opening.html'),'utf8');await p.route('**/__opening-test',r=>r.fulfill({status:200,contentType:'text/html',body:intro}));await go('/__opening-test');assert.equal(await p.locator('html').getAttribute('data-glass'),glass);const logo=p.locator('.kotoba-intro-logo');assert.equal(await logo.evaluate(e=>getComputedStyle(e).backdropFilter==='none'),glass==='off');await p.locator('#kotoba-intro-skip').click();assert.equal(await p.evaluate(()=>window.introSkipped),true);checks++;
 await p.close();console.log('PASS interactive views and native opening preference',glass);
}
// Reduced-memory fallback removes expensive blur everywhere, while retaining glass rims/tints.
const lite=await browser.newPage({viewport:{width:320,height:844}});await lite.addInitScript(()=>{localStorage.setItem('kotoba:onboarding:v3','1');Object.defineProperty(navigator,'deviceMemory',{value:2});window.KotobaStartupNative={introElapsedMs:()=>3000};});await lite.goto('http://127.0.0.1:5059/japan');assert.equal(await lite.locator('html').getAttribute('data-glass-quality'),'lite');assert.equal(await lite.evaluate(()=>[...document.querySelectorAll('body *')].filter(e=>e.getClientRects().length&&getComputedStyle(e).backdropFilter!=='none').length),0);checks++;await lite.close();
assert.deepEqual(errors,[]);fs.writeFileSync(path.join(__dirname,'glass-interactions-results.json'),JSON.stringify({checks,errors,scope:'Desktop browser UI; native opening document and speech bridge simulated. No physical-device audio or Android runtime claim.'},null,2));console.log('All '+checks+' glass interaction checks passed.');await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});

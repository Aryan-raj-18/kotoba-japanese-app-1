const {chromium}=require('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
(async()=>{
 const results=[],errors=[];
 for(const theme of ['sakura-journey','kyoto-night','water-glass'])for(const width of [320,390,600,1180]){
  const browser=await chromium.launch({executablePath:process.env.KOTOBA_CHROME,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process']});
  const context=await browser.newContext({viewport:{width,height:844}});
  await context.addInitScript(theme=>{try{localStorage.setItem('kotoba:theme',theme);}catch(_){}window.KotobaStartupNative={introElapsedMs:()=>3000};
   let state={level:'N5',selected:[],mode:'rotate',minutes:60,meaning:true,readings:true,enabled:false,allowed:true,current:'日'};
   window.KotobaKanjiNotificationNative={getState:()=>JSON.stringify(state),apply:(raw,id)=>{state={...state,...JSON.parse(raw),enabled:true};window.KotobaKanjiNotification.receive(id,state,'');},stop:()=>{state.enabled=false;window.KotobaKanjiNotification.receive('',state,'');},next:()=>{},openSettings:()=>{},openPhoneSettings:()=>{}};
  },theme);
  const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));
  await p.goto('http://127.0.0.1:5059/kanji-notification');await p.locator('#kanji-notification-apply').waitFor({state:'visible'});await p.waitForFunction(()=>!document.getElementById('kanji-notification-apply').disabled);
  await p.locator('#kanji-notification-level').selectOption('N1');await p.waitForFunction(()=>document.querySelectorAll('#kanji-notification-choices input').length===911);
  await p.locator('#kanji-notification-pool').selectOption('selected');await p.locator('#kanji-notification-choices').scrollIntoViewIfNeeded();await p.locator('#kanji-notification-choices').evaluate(e=>{const row=e.querySelectorAll('label')[70];e.scrollTop=row.offsetTop-e.offsetTop-10;});await p.evaluate(()=>window.qaKanjiNode=document.querySelectorAll('#kanji-notification-choices input')[70]);await p.locator('#kanji-notification-choices input').nth(70).check(); const before=await p.locator('#kanji-notification-choices').evaluate(e=>e.scrollTop);assert(before>0); await p.locator('#kanji-notification-choices input').nth(71).check();const after=await p.locator('#kanji-notification-choices').evaluate(e=>e.scrollTop);assert(after>1000&&Math.abs(after-before)<320,JSON.stringify({theme,width,before,after}));
  assert(await p.evaluate(()=>window.qaKanjiNode===document.querySelectorAll('#kanji-notification-choices input')[70]));await p.locator('#kanji-notification-minutes').fill('75');await p.locator('#kanji-notification-apply').click();assert((await p.locator('#kanji-notification-status').innerText()).includes('is active'));
  assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
  await p.locator('#kanji-notification-mode').selectOption('hold');assert(await p.locator('#kanji-notification-duration').isHidden());
  await p.locator('#kanji-notification-stop').click();assert((await p.locator('#kanji-notification-status').innerText()).includes('stopped'));
  if(width===320){await p.addStyleTag({content:'html{font-size:200% !important}'});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);}
  if(theme==='water-glass'&&width===390){await p.evaluate(()=>scrollTo(0,0));await p.screenshot({path:path.join(__dirname,'kanji-notification-build31.png'),fullPage:true});}
  results.push({theme,width,horizontal_overflow:false,N1_cards:911,selection:true,selection_scroll_before:before,selection_scroll_after:after,selection_nodes_retained:true,custom_minutes:75,activation:true,hold:true,stop:true,large_font:width===320});await browser.close();
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(__dirname,'kanji-notification-browser-results.json'),JSON.stringify({layouts:results,errors},null,2));console.log('PASS 12 notification settings layouts, three enlarged-text checks and selection/timing/control interactions');
})().catch(e=>{console.error(e);process.exit(1);});

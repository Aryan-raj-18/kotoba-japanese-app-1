const {chromium}=require('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
(async()=>{const results=[],errors=[];
 for(const theme of ['sakura-journey','kyoto-night','water-glass'])for(const width of [320,390,1180]){
  const browser=await chromium.launch({executablePath:process.env.KOTOBA_CHROME,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process']});
  const context=await browser.newContext({viewport:{width,height:844},hasTouch:width<600,isMobile:width<600});
  await context.addInitScript(theme=>{try{localStorage.setItem('kotoba:theme',theme);localStorage.setItem('kotoba:onboarding:v3','1');}catch(_){}window.KotobaStartupNative={introElapsedMs:()=>3000};window.testSpeech=[];window.KotobaSpeechNative={speak:(text,rate)=>testSpeech.push({text,rate}),stop(){}};},theme);
  const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));
  await p.goto('http://127.0.0.1:5059/roadmap');await p.locator('#chapter-my-family a').scrollIntoViewIfNeeded();const before=await p.evaluate(()=>scrollY);assert(before>1000);
  await p.locator('#chapter-my-family a').click();await p.waitForURL('**/roadmap/my-family');const saved=await p.evaluate(()=>JSON.parse(sessionStorage.getItem('kotoba:roadmap-position:v1')));
  await p.locator('#rm-word-speak').click();const reading=await p.locator('#rm-word-reading').innerText();assert.equal(await p.evaluate(()=>testSpeech.at(-1).text),reading);
  await p.locator('[data-roadmap-return]').click();await p.waitForURL('**/roadmap#chapter-my-family');await p.waitForLoadState('load');await p.evaluate(()=>document.fonts.ready);
  const after=await p.evaluate(()=>scrollY);assert(Math.abs(after-saved.y)<10,JSON.stringify({theme,width,before,saved,after}));
  await p.locator('#chapter-my-family a').click();await p.waitForURL('**/roadmap/my-family');await p.goBack();await p.waitForLoadState('load');const historyReturn=await p.evaluate(()=>scrollY);assert(Math.abs(historyReturn-after)<10,{after,historyReturn});
  await p.goto('http://127.0.0.1:5059/jlpt/N5');await p.locator('[data-kanji="四"]').click();await p.locator('#jlpt-kanji-speak').click();assert.equal(await p.evaluate(()=>testSpeech.at(-1).text),'し');
  const kun=p.locator('#jlpt-reading-audio button').filter({hasText:'Kun-yomi'}).first();const chosen=(await kun.innerText()).split(': ')[1];await kun.click();assert.equal(await p.evaluate(()=>testSpeech.at(-1).text),chosen);assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
  await p.locator('#kanji-modal-close').click();for(const id of [4,75,160]){await p.goto('http://127.0.0.1:5059/kanji/'+id);assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);}
  assert.equal(await p.locator('.detail-actions .speak-btn').getAttribute('data-reading'),'な');assert(!(await p.locator('.reading-list').innerText()).includes('さんねんまえ'));const mei=p.locator('.reading-list button[data-speak="メイ"]');await mei.click();assert.equal(await p.evaluate(()=>testSpeech.at(-1).text),'メイ');
  if(theme==='water-glass'&&width===390)await p.screenshot({path:path.join(__dirname,'kanji-readings-build32.png'),fullPage:true});
  results.push({theme,width,displayed_reading:reading,chosen_kun:chosen,roadmap_before:before,roadmap_after:after,browser_back:historyReturn,horizontal_overflow:false});await browser.close();
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(__dirname,'speech-roadmap-browser-results.json'),JSON.stringify({layouts:results,errors,scope:'Native speech bridge simulated; text input checked, acoustic output requires a physical Android device.'},null,2));console.log('PASS 9 speech/roadmap browser scenarios across three themes and widths; exact return scroll, browser Back, displayed kana and selectable on/kun audio');
})().catch(e=>{console.error(e);process.exit(1);});

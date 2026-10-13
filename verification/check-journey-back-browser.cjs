const {chromium}=require('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const base='http://127.0.0.1:5059';
(async()=>{
 const results=[],errors=[];
 for(const theme of ['sakura-journey','kyoto-night','water-glass'])for(const width of [320,390,1180]){
  const browser=await chromium.launch({executablePath:process.env.KOTOBA_CHROME,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process']});
  const context=await browser.newContext({viewport:{width,height:844},hasTouch:width<600,isMobile:width<600});
  await context.addInitScript(theme=>{try{localStorage.setItem('kotoba:theme',theme);localStorage.setItem('kotoba:onboarding:v3','1');}catch(_){}window.KotobaStartupNative={introElapsedMs:()=>3000};},theme);
  const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));
  async function settled(){await p.waitForLoadState('load');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(100);}
  async function fit(){const geometry=await p.evaluate(()=>({x:scrollX,viewport:innerWidth,content:document.documentElement.scrollWidth,banners:[...document.querySelectorAll('.rm-section-banner')].map(e=>{const r=e.getBoundingClientRect();return {left:r.left,right:r.right};})}));assert.equal(geometry.x,0,JSON.stringify(geometry));assert(geometry.content<=geometry.viewport+1,JSON.stringify(geometry));assert(geometry.banners.every(r=>r.left>=0&&r.right<=geometry.viewport+1),JSON.stringify(geometry));}
  async function home(){const reset=await context.request.post(base+'/api/backup/data',{data:{format:'kotoba-backup-v1',roadmap_completed:[],roadmap_start:'computers-internet'}});assert.equal(reset.status(),200,await reset.text());await p.goto(base+'/');await settled();await p.locator('.journey-chapter').filter({hasText:'Smartphones & Apps'}).scrollIntoViewIfNeeded();}
  async function openPreview(){await p.locator('.journey-chapter').filter({hasText:'Smartphones & Apps'}).click();await p.waitForURL('**/roadmap/smartphones-apps?from=home');await settled();return p.evaluate(()=>JSON.parse(sessionStorage.getItem('kotoba:home-journey-position:v1')).y);}
  async function returnedHome(expected){await p.waitForURL('**/#home-journey');await settled();assert(Math.abs(await p.evaluate(()=>scrollY)-expected)<10,JSON.stringify({theme,width,expected,actual:await p.evaluate(()=>scrollY)}));await fit();}
  await home();let saved=await openPreview();const first=await p.locator('#rm-word-jp').innerText();await p.locator('#rm-next').click();assert.notEqual(await p.locator('#rm-word-jp').innerText(),first);
  await p.evaluate(()=>KotobaNavigation.handleBack());assert.equal(await p.locator('#rm-word-jp').innerText(),first);await p.evaluate(()=>KotobaNavigation.handleBack());await returnedHome(saved);
  saved=await openPreview();await p.locator('#rm-next').click();await p.locator('[data-roadmap-return]').click();await p.locator('[data-leave]').click();await returnedHome(saved);
  saved=await openPreview();await p.goBack();await settled();assert(Math.abs(await p.evaluate(()=>scrollY)-saved)<10);
  saved=await openPreview();const vocab=await p.locator('#rm-vocab-data').textContent();for(const _ of JSON.parse(vocab))await p.locator('#rm-next').click();await p.evaluate(()=>KotobaNavigation.handleBack());await p.locator('[data-leave]').click();await returnedHome(saved);
  // Answer the actual rendered quiz to exercise completion and next-lesson provenance.
  saved=await openPreview();for(const _ of JSON.parse(await p.locator('#rm-vocab-data').textContent()))await p.locator('#rm-next').click();
  const quiz=JSON.parse(await p.locator('#rm-quiz-data').textContent());
  for(const q of quiz){await p.locator('#rm-options').getByRole('button',{name:q.correct,exact:true}).click();await p.locator('#rm-continue').click();}
  await p.locator('#rm-next-chapter').filter({hasText:'Next lesson'}).waitFor();assert((await p.locator('#rm-next-chapter').getAttribute('href')).endsWith('?from=home'));await p.locator('#rm-done .btn-ghost').click();await returnedHome(saved);
  // Continue carries Home origin through a second chapter, whose native Back returns Home.
  saved=await openPreview();for(const _ of JSON.parse(await p.locator('#rm-vocab-data').textContent()))await p.locator('#rm-next').click();
  for(const q of JSON.parse(await p.locator('#rm-quiz-data').textContent())){await p.locator('#rm-options').getByRole('button',{name:q.correct,exact:true}).click();await p.locator('#rm-continue').click();}
  await p.locator('#rm-next-chapter').filter({hasText:'Next lesson'}).click();await settled();assert.equal(await p.evaluate(()=>window.RM_FROM_HOME),true);await p.evaluate(()=>KotobaNavigation.handleBack());await returnedHome(saved);
  // Full roadmap keeps its own exact position and its headings stay on screen.
  await p.goto(base+'/roadmap');await settled();await p.locator('#chapter-smartphones-apps a').scrollIntoViewIfNeeded();await p.locator('#chapter-smartphones-apps a').click();await settled();const roadmapY=await p.evaluate(()=>JSON.parse(sessionStorage.getItem('kotoba:roadmap-position:v1')).y);await p.evaluate(()=>KotobaNavigation.handleBack());await p.waitForURL('**/roadmap#chapter-smartphones-apps');await settled();assert(Math.abs(await p.evaluate(()=>scrollY)-roadmapY)<10);await fit();
  await p.locator('#chapter-smartphones-apps a').click();await settled();await p.goBack();await settled();assert(Math.abs(await p.evaluate(()=>scrollY)-roadmapY)<10);await fit();
  // All chapter offsets can be fragment targets without horizontal panning, including enlarged text.
  const anchors=await p.locator('.rm-node-wrap').evaluateAll(rows=>Object.values(Object.fromEntries(rows.map(e=>[e.style.getPropertyValue('--rm-offset'),e.id]))));
  await p.evaluate(()=>sessionStorage.removeItem('kotoba:roadmap-position:v1'));
  for(const id of anchors){await p.goto(base+'/roadmap#'+id);await settled();await fit();}
  await p.evaluate(()=>document.documentElement.style.fontSize='200%');await fit();
  if(theme==='kyoto-night'&&width===390){await p.goto(base+'/roadmap#chapter-smartphones-apps');await settled();await p.locator('#stage-modern-life').scrollIntoViewIfNeeded();await p.screenshot({path:path.join(__dirname,'journey-back-build33.png')});}
  results.push({theme,width,home_return_y:saved,roadmap_return_y:roadmapY,previous_word:true,native_back:true,header_back:true,quiz_exit:true,completed_back:true,next_lesson_origin:true,browser_back:true,all_offset_anchors:anchors.length,horizontal_overflow:false,enlarged_text_fit:true});await browser.close();
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(__dirname,'journey-back-browser-results.json'),JSON.stringify({layouts:results,errors,scope:'Desktop Chromium; native Back entry point exercised in JavaScript. Physical Android WebView QA pending.'},null,2));console.log('PASS 9 journey-origin/roadmap geometry browser scenarios across three themes and widths; Home and roadmap exact return, previous word, native/header/browser Back, quiz completion/exit, next-lesson origin, all offsets and enlarged text');
})().catch(e=>{console.error(e);process.exit(1);});

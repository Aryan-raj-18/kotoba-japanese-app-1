const {chromium}=require('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
(async()=>{
 const results=[],errors=[];
 for(const theme of ['sakura-journey','kyoto-night','water-glass'])for(const width of [320,390,600]){
  const browser=await chromium.launch({executablePath:process.env.KOTOBA_CHROME,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process']});
  const context=await browser.newContext({viewport:{width,height:844}});
  await context.addInitScript(t=>{try{localStorage.setItem('kotoba:theme',t);}catch(_){}window.KotobaStartupNative={introElapsedMs:()=>3000};},theme);
  const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));
  await p.goto('http://127.0.0.1:5059/');await p.locator('#onboarding-overlay').waitFor({state:'visible'});
  assert.equal(await p.locator('.site-header').evaluate(e=>getComputedStyle(e).display),'none');
  assert.equal(await p.locator('.onboarding-levels > *').count(),5);
  assert.equal(await p.evaluate(()=>localStorage.getItem('kotoba:onboarding:v3')),'1');
  const bounds=await p.locator('.onboarding-card').boundingBox();assert(bounds.x>=0&&bounds.y>=0&&bounds.x+bounds.width<=width+1&&bounds.y+bounds.height<=844+1);
  assert(await p.evaluate(()=>document.documentElement.classList.contains('kotoba-scroll-locked')));
  for(const choice of await p.locator('.onboarding-levels > *').all()){await choice.scrollIntoViewIfNeeded();assert(await choice.isVisible());const b=await choice.boundingBox();assert(b.y>=bounds.y&&b.y+b.height<=bounds.y+bounds.height+1);}
  if(theme==='kyoto-night'&&width===390){await p.locator('.onboarding-card').evaluate(e=>e.scrollTop=0);await p.screenshot({path:path.join(__dirname,'onboarding-build29.png')});}
  if(width===320){await p.locator('#onboarding-skip').click();await p.locator('#onboarding-overlay').waitFor({state:'hidden'});assert.notEqual(await p.locator('.site-header').evaluate(e=>getComputedStyle(e).display),'none');}
  else if(width===390){await p.locator('.onboarding-placement').click();await p.waitForURL('**/placement');await p.goto('http://127.0.0.1:5059/');}
  else{await p.locator('[data-start="/roadmap/hiragana-1"]').click();await p.waitForURL('**/roadmap/hiragana-1');await p.goto('http://127.0.0.1:5059/');}
  await p.reload();await p.waitForTimeout(500);assert(await p.locator('#onboarding-overlay').isHidden());assert(await p.locator('.site-header').isVisible());
  const reopen=await context.newPage();await reopen.goto('http://127.0.0.1:5059/');await reopen.waitForTimeout(500);assert(await reopen.locator('#onboarding-overlay').isHidden());assert(await reopen.locator('.site-header').isVisible());
  results.push({theme,width,choices:5,header_hidden:true,choices_reachable:true,repeat_setup:false,header_restored:true});await browser.close();
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(__dirname,'onboarding-browser-results.json'),JSON.stringify({layouts:results,errors},null,2));console.log('PASS 9 first-launch layouts, dismissal, placement, lesson selection, reload and new-page persistence');
})().catch(e=>{console.error(e);process.exit(1);});

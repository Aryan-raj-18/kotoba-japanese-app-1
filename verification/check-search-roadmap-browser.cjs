const {chromium}=require('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
(async()=>{
 const results=[],errors=[];
 for(const theme of ['sakura-journey','kyoto-night','water-glass'])for(const width of [320,390,600,1180]){
  const browser=await chromium.launch({executablePath:process.env.KOTOBA_CHROME,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process']});
  const context=await browser.newContext({viewport:{width,height:844},isMobile:width<600,hasTouch:width<600});
  await context.addInitScript(theme=>{try{localStorage.setItem('kotoba:theme',theme);localStorage.setItem('kotoba:onboarding:v3','1');}catch(_){}window.KotobaStartupNative={introElapsedMs:()=>3000};},theme);
  const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));
  await p.goto('http://127.0.0.1:5059/');
  const input=p.locator('.home-search-card input[name="q"]');await input.fill('sor');
  const popup=p.locator('.home-search-card .search-suggestions');await popup.waitFor({state:'visible'});
  const sky=popup.locator('a').filter({has:p.locator('strong').filter({hasText:/^空$/})}).filter({hasText:'sora'}).first();
  assert((await sky.innerText()).toLowerCase().includes('sky'));assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
  if(theme==='water-glass'&&width===390){await p.screenshot({path:path.join(__dirname,'search-suggestions-build31.png'),fullPage:true});await popup.screenshot({path:path.join(__dirname,'search-suggestions-panel-build31.png')});}
  const href=await sky.getAttribute('href');await sky.click();await p.waitForURL('**/search/entry/**');assert.equal(await p.locator('.search-entry-word').innerText(),'空');assert((await p.locator('main').innerText()).toLowerCase().includes('sky'));
  await p.goto('http://127.0.0.1:5059/search?q=sor');assert((await p.locator('.search-prefix-results').innerText()).includes('sora'));
  const q=p.locator('.search-page-form input');await q.focus();const list=p.locator('.search-page-form .search-suggestions');await list.waitFor({state:'visible'});await q.press('ArrowDown');assert(await q.getAttribute('aria-activedescendant'));await q.press('Escape');assert(await list.isHidden());
  if(width===1180){await p.locator('.header-search input').fill('sor');await p.locator('.header-search .search-suggestions').waitFor({state:'visible'});}
  results.push({page:'search',theme,width,partial:'sor',correct_word:'空',href,horizontal_overflow:false,keyboard:true,header:width===1180});
  await p.goto('http://127.0.0.1:5059/roadmap');assert.equal(await p.locator('.rm-node').count(),91);assert.equal(await p.locator('.rm-stage-nav a').count(),14);
  assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
  await p.locator('.rm-stage-nav a[href="#stage-n1-mastery"]').click();assert.equal(new URL(p.url()).hash,'#stage-n1-mastery');assert(await p.locator('#stage-n1-mastery').isVisible());
  const top=await p.locator('#stage-n1-mastery').evaluate(e=>e.getBoundingClientRect().top);assert(top>=0&&top<300);
  if(width===320){await p.addStyleTag({content:'html{font-size:200% !important}'});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);}
  if(theme==='water-glass'&&width===390){await p.evaluate(()=>scrollTo(0,0));await p.screenshot({path:path.join(__dirname,'guided-roadmap-build31.png'),fullPage:true});}
  results.push({page:'roadmap',theme,width,chapters:91,stage_links:14,N1_jump:true,horizontal_overflow:false,large_font:width===320});await browser.close();
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(__dirname,'search-roadmap-browser-results.json'),JSON.stringify({layouts:results,errors},null,2));console.log('PASS 24 search/roadmap layouts, three enlarged-text layouts, exact dictionary navigation, keyboard suggestions and N1 stage jumps');
})().catch(e=>{console.error(e);process.exit(1);});

'use strict';
const {JSDOM}=require('jsdom'),{spawnSync}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const pkg=process.env.KOTOBA_TEST_PACKAGE,assets=pkg?path.join(pkg,'kotoba_app'):__dirname;
const code='import tempfile,os;os.environ["KOTOBA_DATA_DIR"]=tempfile.mkdtemp();'+(pkg?`import sys;sys.path.insert(0,${JSON.stringify(pkg)});from kotoba_app.app import app;`:'from app import app;')+'print(app.test_client().get("/").data.decode())';
const result=spawnSync(process.env.KOTOBA_TEST_PYTHON||'python',['-c',code],{cwd:__dirname,encoding:'utf8',maxBuffer:16*1024*1024});assert.equal(result.status,0,result.stderr);
const dom=new JSDOM(result.stdout,{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window,d=w.document;w.localStorage.setItem('kotoba:onboarding:v3','1');w.matchMedia=query=>({matches:query.includes('max-width'),addEventListener(){}});w.Element.prototype.scrollIntoView=function(){};
let checks=0;function check(name,fn){fn();checks++;console.log('PASS '+name);}
(async()=>{
 await new Promise(r=>setImmediate(r));
 for(const name of ['theme-catalog.js','theme.js','home.js'])w.eval(fs.readFileSync(path.join(assets,'static/js',name),'utf8'));
 d.dispatchEvent(new w.Event('DOMContentLoaded'));
 check('daily goal opens Settings and stays open after the click bubbles',()=>{d.getElementById('home-goal-pill').click();assert.equal(d.getElementById('settings-panel').hidden,false);assert.equal(d.getElementById('settings-btn').getAttribute('aria-expanded'),'true');assert(d.getElementById('settings-goal-chips').contains(d.activeElement));});
 check('goal remains usable when Settings is already open',()=>{d.getElementById('home-goal-pill').click();assert.equal(d.getElementById('settings-panel').hidden,false);});
 check('Escape closes the goal settings and returns focus',()=>{d.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Escape',bubbles:true}));assert(d.getElementById('settings-panel').hidden);assert.equal(d.activeElement.id,'settings-btn');});
 check('appearance shows only Light/Dark and no unused palette picker',()=>{
   assert.equal(d.querySelectorAll('#theme-options > .theme-opt').length,2);
   assert.equal(d.querySelectorAll('.theme-more').length,0);
   d.querySelector('[data-theme="kyoto-night"].theme-opt').click();
   assert.equal(w.localStorage.getItem('kotoba:theme'),'kyoto-night');
   assert.equal(d.documentElement.dataset.theme,'kyoto-night');
 });
 check('upcoming chapter preview starts at the actual recommended lesson',()=>{assert.equal(d.querySelector('.journey-chapter').href,d.querySelector('.continue-btn').href);assert.equal(d.querySelectorAll('.journey-chapter').length,3);assert.equal(d.querySelectorAll('.home-stat').length,4);assert.equal(d.querySelectorAll('.focus-card').length,7);});
 check('device appearance resolves to Sakura Journey or Kyoto Night',()=>{w.matchMedia=()=>({matches:false});assert.equal(w.KotobaThemeCatalog.resolve('auto'),'sakura-journey');w.matchMedia=()=>({matches:true});assert.equal(w.KotobaThemeCatalog.resolve('auto'),'kyoto-night');});
 w.close();console.log('All '+checks+' journey home interaction checks passed.');
})().catch(e=>{console.error(e);w.close();process.exitCode=1;});

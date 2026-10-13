'use strict';
const {JSDOM}=require('jsdom'),{spawnSync}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const pkg=process.env.KOTOBA_TEST_PACKAGE,assets=pkg?path.join(pkg,'kotoba_app'):__dirname;
const code='import tempfile,os;os.environ["KOTOBA_DATA_DIR"]=tempfile.mkdtemp();'+(pkg?`import sys;sys.path.insert(0,${JSON.stringify(pkg)});from kotoba_app.app import app;`:'from app import app;')+'print(app.test_client().get("/").data.decode())';
const rendered=spawnSync(process.env.KOTOBA_TEST_PYTHON||'python',['-c',code],{cwd:__dirname,encoding:'utf8',maxBuffer:16*1024*1024});assert.equal(rendered.status,0,rendered.stderr);
const script=fs.readFileSync(path.join(assets,'static/js/home.js'),'utf8');
let count=0;function check(name,fn){fn();count++;console.log('PASS '+name);}
function setup(seen=false,intro=false){
 const dom=new JSDOM(rendered.stdout,{url:'http://localhost/',runScripts:'outside-only'}),w=dom.window,d=w.document,timers=[],requests=[];
 w.setTimeout=f=>{timers.push(f);return timers.length;};
 if(seen)w.localStorage.setItem('kotoba:onboarding:v3','1');
 if(intro)d.body.classList.add('intro-open');
 w.fetch=(url,options)=>{requests.push([url,JSON.parse(options.body)]);return new Promise(()=>{});};
 w.eval(script);return{w,d,timers,requests,show(){timers.shift()();}};
}
check('first launch shows all five choices and records the first appearance',()=>{const t=setup();assert(t.d.getElementById('onboarding-overlay').hidden);assert.equal(t.w.localStorage.getItem('kotoba:onboarding:v3'),null);t.show();assert(!t.d.getElementById('onboarding-overlay').hidden);assert(t.d.body.classList.contains('onboarding-open'));assert.equal(t.d.querySelectorAll('.onboarding-levels > *').length,5);assert.equal(t.w.localStorage.getItem('kotoba:onboarding:v3'),'1');t.w.close();});
check('reopening after leaving without a choice does not show setup again',()=>{const first=setup();first.show();const seen=first.w.localStorage.getItem('kotoba:onboarding:v3');first.w.close();const second=setup(seen);assert.equal(second.timers.length,0);assert(second.d.getElementById('onboarding-overlay').hidden);assert(!second.d.body.classList.contains('onboarding-open'));second.w.close();});
check('existing onboarding preferences remain respected after upgrade',()=>{const t=setup(true);assert.equal(t.timers.length,0);assert(t.d.getElementById('onboarding-overlay').hidden);t.w.close();});
check('placement test choice is already persisted before navigation',()=>{const t=setup();t.show();const link=t.d.querySelector('.onboarding-placement');link.addEventListener('click',e=>e.preventDefault());link.click();assert.equal(link.getAttribute('href'),'/placement');assert.equal(t.w.localStorage.getItem('kotoba:onboarding:v3'),'1');t.w.close();});
check('Skip and outside dismissal restore the ordinary app shell',()=>{for(const target of ['onboarding-skip','onboarding-overlay']){const t=setup();t.show();t.d.getElementById(target).click();assert(t.d.getElementById('onboarding-overlay').hidden);assert(!t.d.body.classList.contains('onboarding-open'));assert.equal(t.w.localStorage.getItem('kotoba:onboarding:v3'),'1');t.w.close();}});
check('each lesson choice still saves its recommended starting chapter',()=>{for(const chapter of ['hiragana-1','greetings-intro','particles-wa-ga-o','n5-kanji-checkpoint']){const t=setup();t.show();const b=[...t.d.querySelectorAll('[data-start]')].find(b=>(b.getAttribute('data-roadmap-start')||b.getAttribute('data-start').split('/').pop())===chapter);assert(b);b.click();assert.deepEqual(t.requests,[['/api/roadmap/start',{chapter_id:chapter}]]);t.w.close();}});
check('setup waits for intro completion and records only its actual appearance',()=>{const t=setup(false,true);assert.equal(t.timers.length,0);assert.equal(t.w.localStorage.getItem('kotoba:onboarding:v3'),null);t.w.dispatchEvent(new t.w.Event('kotoba:intro:done'));assert.equal(t.timers.length,1);t.show();assert.equal(t.w.localStorage.getItem('kotoba:onboarding:v3'),'1');t.w.close();});
check('header hiding is scoped to the open setup panel',()=>{const css=fs.readFileSync(path.join(assets,'static/css/journey.css'),'utf8');assert.match(css,/body\.onboarding-open \.site-header\s*\{\s*display:\s*none\s*!important/);const t=setup();assert(t.d.querySelector('.site-header'));t.w.close();});
console.log('All '+count+' first-launch setup checks passed.');

'use strict';
const {JSDOM}=require('jsdom');
const {spawnSync}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const packageRoot=process.env.KOTOBA_TEST_PACKAGE;
const renderCode=(packageRoot?`import sys; sys.path.insert(0, ${JSON.stringify(packageRoot)}); from kotoba_app.app import app; `:'from app import app; ')+
 'import json; print(json.dumps({level:app.test_client().get("/jlpt/"+level+"/mock").data.decode() for level in ["N5","N4","N3","N2","N1"]}))';
const rendered=spawnSync(process.env.KOTOBA_TEST_PYTHON||'python',['-c',renderCode],{cwd:__dirname,encoding:'utf8'});
assert.equal(rendered.status,0,rendered.stderr);
const pages=JSON.parse(rendered.stdout);
const assetRoot=packageRoot?path.join(packageRoot,'kotoba_app'):__dirname;
const script=fs.readFileSync(path.join(assetRoot,'static/js/jlpt_mock.js'),'utf8');
const css=fs.readFileSync(path.join(assetRoot,'static/css/style.css'),'utf8');
const questions=[
 {id:'q1',prompt:'Choose a word',category:'Vocabulary',options:['一','二','三','四'],answer_index:1,explanation:'Two'},
 {id:'q2',prompt:'Choose a sentence',category:'Grammar',options:['Option A','Option B','Option C','Option D'],answer_index:2,explanation:'Reviewed example'}
];
const settle=()=>new Promise(resolve=>setImmediate(resolve));
let checks=0;
async function setup(level='N5',holdSave=false){
 const dom=new JSDOM(pages[level],{url:'http://localhost/jlpt/'+level+'/mock',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window,d=w.document;await settle();
 const style=d.createElement('style');style.textContent=css;d.head.append(style);
 const errors=[],saves=[],records=[];w.addEventListener('error',e=>errors.push(e.message));
 let now=0,tick,resolveSave;
 w.Date.now=()=>now;w.setInterval=fn=>{tick=fn;return 1;};w.clearInterval=()=>{};
 w.fetch=async(url,opts)=>{
  if(opts){saves.push(JSON.parse(opts.body));if(holdSave)await new Promise(resolve=>resolveSave=resolve);return {ok:true,json:async()=>({ok:true})};}
  return {ok:true,json:async()=>({questions})};
 };
 w.KotobaLearn={record:value=>{records.push(value);return Promise.resolve();}};
 w.eval(script);d.dispatchEvent(new w.Event('DOMContentLoaded'));
 d.getElementById('mock-start').click();await settle();
 return {dom,w,d,errors,saves,records,buttons:()=>[...d.querySelectorAll('#mock-options button')],expire:async()=>{now=1e9;tick();await settle();},release:async()=>{resolveSave();await settle();}};
}
function check(name,fn){fn();checks++;console.log('PASS '+name);}
(async()=>{
 for(const level of Object.keys(pages)){
  const t=await setup(level);
  check(level+' accepts every option and visibly retains changes across questions',()=>{
   assert.equal(t.d.getElementById('mock-results').hidden,true);
   const normal=t.w.getComputedStyle(t.buttons()[0]).fontWeight;
   for(let i=0;i<4;i++){
    const b=t.buttons()[i];b.focus();b.click();
    assert.equal(t.d.activeElement,b,'Choosing an option must preserve keyboard focus');
    assert.equal(t.buttons().filter(x=>x.classList.contains('selected')).length,1);
    assert.equal(b.getAttribute('aria-pressed'),'true');
    assert.equal(b.querySelector('.mock-choice-indicator').hidden,false);
    assert.equal(t.w.getComputedStyle(b).fontWeight,'700','Selection needs visible styling');
    assert.notEqual(t.w.getComputedStyle(b).fontWeight,normal);
    assert.match(t.d.getElementById('mock-selection').textContent,new RegExp('Selected option '+(i+1)));
    assert(t.buttons().every(x=>!x.disabled));
   }
   assert.equal(t.buttons().filter(x=>x.getAttribute('aria-pressed')==='false').length,3);
   assert.equal(t.saves.length,0);assert.equal(t.records.length,0,'No answers graded before submission');
   t.d.getElementById('mock-next').click();assert.equal(t.buttons().filter(x=>x.classList.contains('selected')).length,0);
   t.buttons()[2].click();t.d.getElementById('mock-prev').click();
   assert.equal(t.buttons()[3].getAttribute('aria-pressed'),'true');
   t.buttons()[1].click();t.d.getElementById('mock-flag').click();
   assert.equal(t.buttons()[1].getAttribute('aria-pressed'),'true');
   t.d.querySelectorAll('#mock-palette button')[1].click();assert.equal(t.buttons()[2].getAttribute('aria-pressed'),'true');
   t.d.querySelectorAll('#mock-palette button')[0].click();assert.equal(t.buttons()[1].getAttribute('aria-pressed'),'true');
   assert.equal(t.errors.length,0);
  });
  t.dom.window.close();
 }
 let t=await setup('N3',true);
 t.buttons()[0].click();t.buttons()[1].click();t.d.getElementById('mock-next').click();t.buttons()[2].click();
 t.d.getElementById('mock-submit').click();t.d.getElementById('mock-submit').click();
 check('submission saves the latest selected answers once and freezes choices',()=>{
  assert.equal(t.saves.length,1);assert.equal(t.saves[0].score,2);assert(t.buttons().every(x=>x.disabled));
 });
 await t.release();
 check('results show the choices the learner actually selected',()=>{
  assert.equal(t.d.getElementById('mock-results').hidden,false);assert.equal(t.records.length,2);
  assert.equal(t.records[0].chosen,'二');assert.equal(t.records[1].chosen,'Option C');
  assert.match(t.d.getElementById('mock-review').textContent,/Your answer: 二/);
 });t.dom.window.close();
 t=await setup('N1');t.buttons()[1].click();await t.expire();await t.expire();
 check('timeout grades the selected answer and preserves unanswered questions',()=>{
  assert.equal(t.saves.length,1);assert.equal(t.saves[0].score,1);
  assert.match(t.d.getElementById('mock-score').textContent,/time ended/);
  assert.equal(t.records[0].chosen,'二');assert.equal(t.records[1].chosen,'Unanswered');assert.equal(t.errors.length,0);
 });t.dom.window.close();
 console.log('All '+checks+' JLPT mock interaction checks passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});

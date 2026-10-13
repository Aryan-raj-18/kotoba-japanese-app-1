'use strict';
// Lightweight no-dependency browser-logic regression for the scenario filter.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const nodes=Object.create(null);
function node(id){return nodes[id] ||= {id,hidden:false,disabled:false,textContent:'',value:'all',currentTime:0,
 classList:{add(){},remove(){}},listeners:{},addEventListener(type,fn){this.listeners[type]=fn},
 click(){return this.onclick?.()},pause(){}};}
const sourceButtons=['all','phrasebook','course'].map(s=>Object.assign(node('source-'+s),{dataset:{source:s}}));
const levelButtons=['all','easy','medium','hard'].map(s=>Object.assign(node('level-'+s),{dataset:{level:s}}));
const selfButtons=['retry','good'].map(s=>Object.assign(node('self-'+s),{dataset:{self:s}}));
const docListeners={};
const document={getElementById:node,addEventListener(type,cb){docListeners[type]=cb},
 querySelectorAll(q){return q.includes('#speaking-sources')?sourceButtons:q.includes('#speaking-levels')?levelButtons:q==='[data-self]'?selfButtons:[]}};
let lastUrl='';
const window={addEventListener(){},KotobaSpeech:{stop(){}}};
const ctx={document,window,URL:{revokeObjectURL(){}},fetch:async u=>{lastUrl=u;return{ok:true,json:async()=>({items:[{id:'one',level:'easy',jp:'今朝は六時に起きました。',reading:'けさはろくじにおきました',romaji:'kesa wa rokuji ni okimashita',english:'I got up at six this morning.',source:'Everyday scenarios · Morning routines'}]})}},encodeURIComponent};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'static/js/speaking.js'),'utf8'),ctx);
assert.equal(typeof docListeners.DOMContentLoaded,'function');
docListeners.DOMContentLoaded();
(async()=>{
 assert.equal(node('speaking-situations').hidden,false); // start state from mock defaults; actual markup has hidden
 sourceButtons[1].listeners.click();
 assert.equal(node('speaking-situations').hidden,false);
 node('speaking-category').value='Learning Japanese';
 levelButtons[1].listeners.click();
 await node('speaking-start').click();
 assert.match(lastUrl,/source=phrasebook/);
 assert.match(lastUrl,/category=Learning%20Japanese/);
 assert.match(lastUrl,/level=easy/);
 assert.match(node('speaking-jp').textContent,/今朝は六時/);
 sourceButtons[2].listeners.click();
 assert.equal(node('speaking-situations').hidden,true);
 assert.equal(node('speaking-category').value,'all');
 await node('speaking-start').click();
 assert.match(lastUrl,/source=course/);
 assert.match(lastUrl,/category=all/);
 console.log('PASS: selecting, applying and resetting original-speaking situation filters');
})().catch(e=>{console.error(e);process.exitCode=1;});

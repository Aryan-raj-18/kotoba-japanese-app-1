'use strict';
const {JSDOM}=require('jsdom'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const assets=process.env.KOTOBA_TEST_PACKAGE?path.join(process.env.KOTOBA_TEST_PACKAGE,'kotoba_app'):__dirname;
const script=fs.readFileSync(path.join(assets,'static/js/search-suggestions.js'),'utf8');
let checks=0;const pause=()=>new Promise(r=>setTimeout(r,180));
function check(name,fn){fn();checks++;console.log('PASS '+name);}
function setup(){
 const dom=new JSDOM('<form class="header-search"><input name="q"><button>Search</button></form><form class="hero-search"><input name="q"></form><form class="hero-search"><input name="q"></form><button id="outside">Elsewhere</button>',{url:'http://localhost/',runScripts:'outside-only'}),w=dom.window,d=w.document,calls=[];
 w.fetch=(url,options)=>new Promise((resolve,reject)=>calls.push({url,options,resolve,reject}));w.eval(script);
 return {w,d,calls,input:d.querySelector('input'),panel:d.querySelector('.search-suggestions'),type(value){this.input.focus();this.input.value=value;this.input.dispatchEvent(new w.Event('input'));},reply(i,rows=[{word:'空',reading:'そら',romaji:'sora',meaning:'sky',href:'/search/entry/abcdef',kind:'Word'}]){calls[i].resolve({ok:true,json:async()=>rows});},close(){w.close();}};
}
(async()=>{
 let t=setup();check('header, home and search forms all get accessible suggestions',()=>{assert.equal(t.d.querySelectorAll('[role="combobox"]').length,3);assert.equal(t.d.querySelectorAll('[role="listbox"]').length,3);});
 t.type('so');t.type('sor');await pause();check('typing is debounced into one offline prefix request',()=>{assert.equal(t.calls.length,1);assert(t.calls[0].url.endsWith('q=sor'));});t.reply(0);await pause();
 check('sor displays sora and its precise dictionary destination',()=>{assert(!t.panel.hidden);assert(t.panel.textContent.includes('sora'));assert.equal(t.panel.querySelector('a').getAttribute('href'),'/search/entry/abcdef?q=sor');});
 t.input.dispatchEvent(new t.w.KeyboardEvent('keydown',{key:'ArrowDown',cancelable:true}));check('keyboard choice updates the active option without losing input focus',()=>{assert.equal(t.input.getAttribute('aria-activedescendant'),t.panel.querySelector('a').id);assert.equal(t.d.activeElement,t.input);});
 t.input.dispatchEvent(new t.w.KeyboardEvent('keydown',{key:'Escape'}));check('Escape dismisses the list and clears accessibility state',()=>{assert(t.panel.hidden);assert.equal(t.input.getAttribute('aria-expanded'),'false');assert(!t.input.hasAttribute('aria-activedescendant'));});
 t.type('wat');await pause();t.type('sor');await pause();t.reply(1,[{word:'水',meaning:'water',href:'/search/entry/123abc'}]);await pause();check('late responses cannot replace the newest prefix',()=>{assert(t.panel.textContent.includes('sora'));assert(!t.panel.textContent.includes('水'));assert(t.calls[1].options.signal.aborted);});
 t.type('');check('clearing search immediately closes suggestions',()=>assert(t.panel.hidden));t.close();
 t=setup();t.type('sor');await pause();t.d.getElementById('outside').focus();t.reply(0);await pause();check('a response after focus leaves the form cannot reopen the popup',()=>assert(t.panel.hidden));t.close();
 t=setup();t.input.focus();t.input.dispatchEvent(new t.w.CompositionEvent('compositionstart'));t.type('そ');await pause();assert.equal(t.calls.length,0);t.input.dispatchEvent(new t.w.CompositionEvent('compositionend'));await pause();t.reply(0);await pause();check('Japanese IME waits until composition is committed',()=>{assert.equal(t.calls.length,1);assert(!t.panel.hidden);});t.w.dispatchEvent(new t.w.Event('kotoba-voice-search-start'));check('starting voice search dismisses typed suggestions',()=>assert(t.panel.hidden));t.close();
 t=setup();t.type('sor');await pause();t.reply(0,[{word:'<img src=x onerror=alert(1)>',meaning:'<script>unsafe</script>',href:'/search/entry/abcdef'},{word:'bad',href:'javascript:alert(1)'}]);await pause();check('dictionary text is rendered safely and unsafe links are discarded',()=>{assert.equal(t.panel.querySelectorAll('a').length,1);assert(!t.panel.querySelector('img'));assert(!t.panel.querySelector('script'));});t.close();
 t=setup();t.type('sor');await pause();t.calls[0].reject(Error('offline failure'));await pause();check('failed suggestions leave the original search form usable',()=>{assert(t.panel.hidden);assert.equal(t.input.value,'sor');assert(t.input.form.querySelector('button'));});t.close();
 console.log('All '+checks+' search suggestion interaction checks passed.');
})().catch(e=>{console.error(e);process.exit(1);});

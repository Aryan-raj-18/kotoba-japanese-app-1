'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=process.env.KOTOBA_TEST_PACKAGE?path.join(process.env.KOTOBA_TEST_PACKAGE,'kotoba_app'):__dirname;
const file=(p)=>fs.readFileSync(path.join(root,p),'utf8');
const base=file('templates/base.html'),css=file('static/css/liquid-glass.css'),js=file('static/js/liquid-glass.js');
assert(base.includes("filename='css/liquid-glass.css'"));
assert(base.includes("filename='js/liquid-glass.js'"));
assert(base.includes('id="liquid-glass-switch"'));
assert(base.includes("localStorage.getItem('kotoba:liquid-glass') === 'off'"));
assert(css.includes('[data-glass="on"]'));
assert(css.includes('prefers-reduced-motion: reduce'));
assert(css.includes('prefers-reduced-transparency: reduce'));
assert(css.includes('[data-glass-quality="lite"]'));
assert(css.includes('.rm-option:not(.rm-correct):not(.rm-wrong)'));
assert(!/canvas|requestAnimationFrame|setInterval/.test(js));
assert(!js.includes('feDisplacementMap'), 'Unsafe displaced SVG layer must stay disabled');
assert(!js.includes('createElementNS'), 'No SVG distortion element should be inserted');
assert(js.includes('liquid-glass-react'), 'Upstream attribution should be retained');
assert(fs.existsSync(path.join(root,'static/vendor/liquid-glass-react/LICENSE')));
const shell=file('static/sw.js');
assert(shell.includes('/static/css/liquid-glass.css'));
assert(shell.includes('/static/js/liquid-glass.js'));
assert(shell.includes('/static/js/ripple.js'));
for(const p of ['templates/base.html','static/css/liquid-glass.css','static/js/liquid-glass.js','static/js/ripple.js','static/sw.js']){
  const mirrored=fs.readFileSync(path.join(__dirname,'android/app/src/main/python/kotoba_app',p),'utf8');
  assert.equal(mirrored,fs.readFileSync(path.join(__dirname,p),'utf8'),p+' mirror drift');
}
function session(initial,memory) {
  const saved=new Map(initial==='off'?[['kotoba:liquid-glass','off']]:[]),attributes=new Map();
  const on={};
  const toggle={setAttribute:(k,v)=>attributes.set(k,v),addEventListener:(e,cb)=>on[e]=cb};
  const window={CSS:{supports:()=>false},matchMedia:()=>({matches:false})};
  const context={window,CSS:window.CSS,document:{documentElement:{setAttribute:(k,v)=>attributes.set('root-'+k,v),getAttribute:k=>attributes.get('root-'+k)||null},getElementById:id=>id==='liquid-glass-switch'?toggle:null},
    localStorage:{getItem:k=>saved.get(k)??null,setItem:(k,v)=>saved.set(k,v)},
    navigator:{deviceMemory:memory},window:window};
  vm.runInNewContext(js,context);
  return {saved,attributes,click:()=>on.click()};
}
let s=session(null,8);
assert.equal(s.attributes.get('aria-checked'),'true');
assert.equal(s.attributes.get('root-data-glass'),'on');
s.click();assert.equal(s.saved.get('kotoba:liquid-glass'),'off');assert.equal(s.attributes.get('root-data-glass'),'off');
s.click();assert.equal(s.saved.get('kotoba:liquid-glass'),'on');assert.equal(s.attributes.get('root-data-glass'),'on');
s=session('off',2);
assert.equal(s.attributes.get('root-data-glass'),'off');
assert.equal(s.attributes.get('root-data-glass-quality'),'lite');
assert.equal(s.attributes.get('aria-checked'),'false');
console.log('PASS liquid glass defaults, switch persistence, reduced-memory mode, accessibility styles and native asset parity');

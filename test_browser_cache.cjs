// Offline cache routing, without a network or browser rendering claim.
const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=process.env.KOTOBA_TEST_PACKAGE?path.join(process.env.KOTOBA_TEST_PACKAGE,'kotoba_app'):__dirname;
const script=fs.readFileSync(path.join(root,'static/sw.js'),'utf8'),
      build=(fs.readFileSync(path.join(root,'app.py'),'utf8').match(/ASSET_BUILD\s*=\s*["'](\d+)["']/)||[])[1];
assert(build, 'Application must publish a cache version');
const listeners={},calls=[],cached={body:'cached CSS'},cache={addAll:async paths=>{assert(paths.every(p=>p.endsWith('?v='+build)));calls.push('install');},match:async(req,opt)=>{assert.equal(opt.ignoreSearch,true);calls.push(req.url);return cached;}};
vm.runInNewContext(script,{URL,self:{location:{origin:'http://localhost'},addEventListener:(n,f)=>listeners[n]=f,skipWaiting(){},clients:{claim(){}}},fetch:async()=>{throw Error('offline');},caches:{open:async name=>{assert.equal(name,'kotoba-shell-v100-build'+build);return cache;}},Promise});
(async()=>{let result;listeners.install({waitUntil:p=>result=p});await result;console.log('PASS shell precaches the current versioned assets');
 listeners.fetch({request:{method:'GET',url:'http://localhost/static/css/style.css?v='+build},respondWith:p=>result=p});assert.equal(await result,cached);console.log('PASS offline versioned requests use the current cache fallback');
 for(const url of ['http://localhost/api/backup/data','http://localhost/kanji','https://external.invalid/static/other.js'])listeners.fetch({request:{method:'GET',url},respondWith(){throw Error('personal or external request intercepted');}});console.log('PASS personal pages, APIs and external requests bypass the cache');console.log('All 3 browser-cache routing checks passed.');})().catch(e=>{console.error(e);process.exitCode=1;});

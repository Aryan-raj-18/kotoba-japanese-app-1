(function () {
  'use strict';
  const keys=['kotoba:theme','kotoba:daily-goal-minutes','kotoba:sound','kotoba:haptics','kotoba:voice-search-language'];
  let busy=false, lastSettings='', timer;
  function settings(){const out={};try{keys.forEach(k=>{const v=localStorage.getItem(k);if(v!==null)out[k]=v;});}catch(_){}return out;}
  function csrf(){return document.querySelector('meta[name="csrf-token"]')?.content||'';}
  async function post(url,data){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...data,csrf_token:csrf()})});const out=await r.json();if(!r.ok)throw Error(out.error||'Could not update cloud sync.');return out;}
  function render(out){
    const el=document.getElementById('cloud-sync-status'),toggle=document.getElementById('cloud-sync-switch');
    if(toggle){toggle.disabled=!out.configured;toggle.setAttribute('aria-checked',String(out.enabled));}
    const messages={local:out.configured?'Cloud sync is off. Progress saves on this device.':'Cloud sync is not available in this build. Progress saves on this device, online or offline.',syncing:'Progress is saved on this device. Syncing the cloud copy…',synced:'Progress is saved on this device and synced to the cloud.',waiting:'Progress is saved on this device. Cloud sync will retry when internet or the service returns.',conflict:'Both copies are kept. Choose which progress to use.',deleted:'Cloud copy was removed. Your local progress is kept.'};
    if(el)el.textContent=out.message||messages[out.state]||messages.waiting;
    const date=document.getElementById('cloud-last-sync');if(date)date.textContent=out.last_synced?'Last cloud save: '+new Date(out.last_synced*1000).toLocaleString():'';
    const conflict=document.getElementById('cloud-conflict');if(conflict)conflict.hidden=out.state!=='conflict';
    const deletion=document.getElementById('cloud-delete');if(deletion)deletion.hidden=!out.configured;
    const connection=document.getElementById('cloud-connection');if(connection)connection.hidden=!out.configured;
    try{
      const marker='kotoba:cloud-settings:'+out.profile;
      if(out.remote_settings_version&&localStorage.getItem(marker)!==out.remote_settings_version){
        keys.forEach(k=>{if(typeof out.remote_settings?.[k]==='string')localStorage.setItem(k,out.remote_settings[k]);});
        localStorage.setItem(marker,out.remote_settings_version);lastSettings=JSON.stringify(settings());
        window.KotobaLearn?.toast('Cloud progress received. Reopen this section to refresh.');
      }
    }catch(_){}
  }
  async function pulse(){
    if(busy||document.visibilityState==='hidden')return;
    busy=true;
    try{
      let r=await fetch('/api/cloud/status',{cache:'no-store'});if(!r.ok)throw Error('Local connection unavailable. Reopen Kotoba; saved progress is kept.');
      let out=await r.json();render(out);
      const text=JSON.stringify(settings());
      if(out.configured&&out.enabled&&text!==lastSettings){out=await post('/api/cloud/settings',{settings:settings()});lastSettings=text;render(out);}
    }catch(e){const el=document.getElementById('cloud-sync-status');if(el)el.textContent=e.message;}
    finally{busy=false;}
  }
  document.addEventListener('DOMContentLoaded',()=>{
    pulse();timer=setInterval(pulse,15000);
    document.getElementById('cloud-sync-switch')?.addEventListener('click',async e=>{
      const el=e.currentTarget;el.disabled=true;
      try{const out=await post('/api/cloud/settings',{enabled:el.getAttribute('aria-checked')!=='true',settings:settings()});render(out);}
      catch(error){document.getElementById('cloud-sync-status').textContent=error.message;el.disabled=false;}
    });
    document.querySelectorAll('[data-cloud-choice]').forEach(b=>b.addEventListener('click',async()=>{
      if(window.prompt('This replaces one progress copy. Type REPLACE to continue.')!=='REPLACE')return;
      try{render(await post('/api/cloud/resolve',{choice:b.dataset.cloudChoice,confirm:'REPLACE'}));}catch(e){document.getElementById('cloud-sync-status').textContent=e.message;}
    }));
    document.getElementById('cloud-delete')?.addEventListener('click',async()=>{
      if(window.prompt('Delete the cloud copy and turn sync off? Local progress is kept. Type DELETE CLOUD to continue.')!=='DELETE CLOUD')return;
      try{render(await post('/api/cloud/delete',{confirm:'DELETE CLOUD'}));}catch(e){document.getElementById('cloud-sync-status').textContent=e.message;}
    });
    document.getElementById('cloud-save-key')?.addEventListener('click',async()=>{
      if(!window.confirm('Save a private key that gives access to your cloud progress? Keep it private and share only with your own devices.'))return;
      try{
        const data=await post('/api/cloud/key',{confirm:'SAVE KEY'}),text=JSON.stringify(data,null,2),name='kotoba-private-cloud-key.json';
        if(window.KotobaBackupNative){window.KotobaBackupNative.saveBackup(name,text);return;}
        const url=URL.createObjectURL(new Blob([text],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);
      }catch(e){document.getElementById('cloud-sync-status').textContent=e.message;}
    });
    document.getElementById('cloud-connect-key')?.addEventListener('click',async()=>{
      const file=document.getElementById('cloud-key-file').files[0];
      if(!file){document.getElementById('cloud-sync-status').textContent='Choose your private Kotoba cloud key first.';return;}
      if(window.prompt('Keep a backup of this device before connecting. Type CONNECT to use the cloud progress from this key.')!=='CONNECT')return;
      try{if(file.size>16384)throw Error('This is not a cloud key file.');const connection=JSON.parse(await file.text());render(await post('/api/cloud/connect',{connection,confirm:'CONNECT'}));}
      catch(e){document.getElementById('cloud-sync-status').textContent=e.message;}
    });
    window.addEventListener('kotoba-backup-status',e=>{const el=document.getElementById('cloud-sync-status');if(el)el.textContent=e.detail;});
  });
  // Internet state is not used to gate local saves: loopback works in airplane mode.
  window.addEventListener('online',pulse);
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')pulse();});
  window.addEventListener('pagehide',()=>clearInterval(timer));
  window.addEventListener('pageshow',e=>{if(e.persisted){clearInterval(timer);timer=setInterval(pulse,15000);pulse();}});
})();

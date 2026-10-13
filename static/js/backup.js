document.addEventListener('DOMContentLoaded',()=>{
 const status=document.getElementById('backup-status'),exportButton=document.getElementById('backup-export');
 window.addEventListener('kotoba-backup-status',e=>{status.textContent=e.detail;exportButton.disabled=false;});
 exportButton.addEventListener('click',async()=>{
  exportButton.disabled=true;status.textContent='Preparing backup…';
  try{const r=await fetch('/api/backup/data');if(!r.ok)throw new Error('Could not read learning data');const data=await r.json();
   data.browser_settings={};for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k&&k.startsWith('kotoba:'))data.browser_settings[k]=localStorage.getItem(k);}
   const text=JSON.stringify(data,null,2),filename=`kotoba-backup-${new Date().toISOString().slice(0,10)}.json`;
   if(window.KotobaBackupNative){status.textContent='Choose where to save your backup…';window.KotobaBackupNative.saveBackup(filename,text);return;}
   const url=URL.createObjectURL(new Blob([text],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);status.textContent='Backup download started.';
  }catch(e){status.textContent=e.message||'Could not export backup';}
  exportButton.disabled=false;
 });
 document.getElementById('backup-import').addEventListener('click',async()=>{
  const f=document.getElementById('backup-file').files[0];if(!f){status.textContent='Choose a backup file first.';return;}
  try{if(f.size>20*1024*1024)throw new Error('Backup is too large');const data=JSON.parse(await f.text());const settings=data.browser_settings||{};
   if(typeof settings!=='object'||Array.isArray(settings)||Object.entries(settings).some(([k,v])=>!k.startsWith('kotoba:')||typeof v!=='string'))throw new Error('Invalid backup settings');
   const r=await fetch('/api/backup/data',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const out=await r.json();if(!r.ok)throw new Error(out.error||'Restore failed');
   let restoredSettings=true;try{Object.entries(settings).forEach(([k,v])=>localStorage.setItem(k,v));}catch(_){restoredSettings=false;}
   status.textContent=restoredSettings?'Backup restored. Reloading…':'Learning progress restored. Some settings could not fit on this device.';setTimeout(()=>location.href='/',1500);
  }catch(e){status.textContent=e.message||'Could not read that backup.';}
 });
});

(function(){
  'use strict';
  var overlay=document.getElementById('kotoba-intro');
  if(!overlay){ window.setTimeout(function(){window.dispatchEvent(new CustomEvent('kotoba:intro:done'));},0); return; }
  var SESSION='kotoba:intro:session:v1';
  var INTRO_TOTAL_MS=3000, LEAVE_MS=360;
  var elapsed=0;
  try{if(window.KotobaStartupNative&&window.KotobaStartupNative.introElapsedMs)elapsed=Math.max(0,Number(window.KotobaStartupNative.introElapsedMs())||0);}catch(_){}
  var sessionSeen=false;
  try{ sessionSeen=sessionStorage.getItem(SESSION)==='1'; }catch(e){}
  function done(){
    if(overlay.hidden) return;
    overlay.classList.add('is-leaving');
    document.body.classList.remove('intro-open');
    window.setTimeout(function(){ overlay.hidden=true; overlay.remove(); window.dispatchEvent(new CustomEvent('kotoba:intro:done')); },LEAVE_MS);
  }
  // Show the opening animation once per app/WebView session. This means it is
  // present on every cold app launch, but it does not replay while navigating
  // back to Home during the same session.
  if(sessionSeen||elapsed>=INTRO_TOTAL_MS){
    try{sessionStorage.setItem(SESSION,'1');}catch(_){}
    overlay.hidden=true;
    overlay.remove();
    window.setTimeout(function(){window.dispatchEvent(new CustomEvent('kotoba:intro:done'));},0);
    return;
  }
  try{ sessionStorage.setItem(SESSION,'1'); }catch(e){}
  document.body.classList.add('intro-open');
  overlay.hidden=false;
  // Continue the same opening timeline after the local server is ready.
  if(elapsed&&overlay.getAnimations){overlay.getAnimations({subtree:true}).forEach(function(a){try{a.currentTime=elapsed;}catch(_){}});}
  var skip=document.getElementById('kotoba-intro-skip');
  if(skip) skip.addEventListener('click',done);
  window.setTimeout(done,Math.max(0,INTRO_TOTAL_MS-LEAVE_MS-elapsed));
})();

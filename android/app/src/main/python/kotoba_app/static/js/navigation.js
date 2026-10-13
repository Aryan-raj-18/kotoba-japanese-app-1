/* Back follows the current learning screen before using page history. */
(function(){
 'use strict';
 let dialog=null,focus=null;
 const sessions=[
  ['panel-intro','panel-done','learn-prev'],['mcq-panel-intro','mcq-panel-results'],
  ['fc-intro','fc-done'],['exam-panel-intro','exam-panel-results'],
  ['mock-intro','mock-results','mock-prev'],['review-intro','review-done'],
  ['speaking-intro','speaking-done'],['placement-intro','placement-done'],
  ['game-picker','game-again'],['rm-learn','rm-done','rm-prev']
 ];
 const el=id=>document.getElementById(id);
 function visible(node){if(!node?.isConnected)return false;for(let p=node;p?.nodeType===1;p=p.parentElement)if(p.hidden||p.getAttribute('aria-hidden')==='true'||p.style.display==='none')return false;return true;}
 function session(){return sessions.find(([start,end,prev])=>el(start)&&(!visible(el(start))||(prev&&visible(el(prev))&&!el(prev).disabled)));}
 function close(){dialog?.remove();dialog=null;if(focus?.isConnected)focus.focus();}
 function leave(action){
  if(dialog)return;focus=document.activeElement;dialog=document.createElement('div');dialog.className='practice-exit-overlay';
  dialog.innerHTML='<section class="practice-exit-dialog" role="dialog" aria-modal="true" aria-labelledby="practice-exit-title"><h2 id="practice-exit-title">Leave this practice round?</h2><p>Your saved progress stays on this device. This unfinished round will end.</p><div class="modal-actions"><button type="button" class="btn-primary" data-stay>Keep practicing</button><button type="button" class="btn-ghost" data-leave>Leave round</button></div></section>';
  document.body.append(dialog);const stay=dialog.querySelector('[data-stay]'),exit=dialog.querySelector('[data-leave]');stay.onclick=close;exit.onclick=()=>{close();window.KotobaSpeech?.stop();action();};dialog.onclick=e=>{if(e.target===dialog)close();};
  dialog.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();close();}else if(e.key==='Tab'){e.preventDefault();(document.activeElement===stay?exit:stay).focus();}};stay.focus();
 }
 function kanjiBack(){
  const link=document.querySelector('[data-kanji-return]');if(!link)return false;
  const source=document.createElement('a');source.href=document.referrer;
  if(document.referrer&&source.origin===link.origin&&source.pathname==='/kanji'&&window.history.length>1)window.history.back();
  else window.location.assign(link.href);
  return true;
 }
 function handleBack(){
  window.KotobaSpeech?.stop();
  if(dialog){close();return true;}
  for(const [panel,button]of [['wallpaper-crop-overlay','wallpaper-crop-close'],['voice-search-overlay','voice-search-close'],['kana-modal','kana-modal-close'],['kanji-modal','kanji-modal-close'],['word-modal','modal-close'],['verb-modal','verb-modal-close'],['japan-passport-modal','japan-passport-close'],['japan-drawer','japan-drawer-close'],['settings-panel','settings-btn']])if(visible(el(panel))&&el(button)){el(button).click();return true;}
  if(el('japan-map-wrap')?.classList.contains('is-expanded')&&el('japan-map-expand')){el('japan-map-expand').click();return true;}
  if(kanjiBack())return true;
  const s=session();if(!s){if(visible(el('flash-mode'))){document.querySelector('.mode-btn[data-mode="chart"]')?.click();return true;}if(el('rm-learn')){window.location.assign(document.querySelector('[data-roadmap-return]')?.href||'/roadmap');return true;}return false;}
  const prev=el(s[2]);if(visible(prev)&&!prev.disabled){prev.click();return true;}
  if(el('rm-learn')){const target=document.querySelector('[data-roadmap-return]')?.href||'/roadmap';if(visible(el(s[1])))window.location.assign(target);else leave(()=>window.location.assign(target));return true;}
  if(visible(el(s[1])))window.location.reload();else leave(()=>window.location.reload());return true;
 }
 function goBack(){if(handleBack())return;if(window.history.length>1){window.history.back();return;}const parent=document.querySelector('main .back-link'),p=window.location.pathname;window.location.assign(parent?.href||(p.startsWith('/jlpt/')?'/jlpt':p.startsWith('/roadmap/')?'/roadmap':['/review','/flashcards'].includes(p)?'/review':'/explore'));}
 window.KotobaNavigation={handleBack,goBack};
 document.addEventListener('DOMContentLoaded',()=>{
  el('page-back')?.addEventListener('click',goBack);
  document.addEventListener('click',e=>{const link=e.target.closest?.('a.back-link'),s=session();if(link?.hasAttribute('data-kanji-return')&&!e.ctrlKey&&!e.metaKey&&!e.shiftKey&&!e.altKey&&e.button===0){e.preventDefault();kanjiBack();return;}if(!link||!s||visible(el(s[1]))||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey||e.button!==0)return;e.preventDefault();leave(()=>window.location.assign(link.href));});
 });
})();

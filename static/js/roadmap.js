/* Roadmap path page: locked / coming-soon nodes can't be opened, so give
   a short message instead of a dead tap. */
(function () {
  'use strict';
  var toast = document.getElementById('rm-toast');
  var timer = null;

  function say(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.hidden = false;
    clearTimeout(timer);
    timer = setTimeout(function () { toast.hidden = true; }, 2200);
  }

  document.querySelectorAll('.rm-node.rm-locked').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var title = btn.getAttribute('data-title');
      if (btn.getAttribute('data-soon') === 'yes') {
        say(title + ' is coming soon.');
      } else {
        say('Finish the chapter before this one to unlock ' + title + '.');
      }
      btn.classList.remove('rm-shake');
      void btn.offsetWidth;
      btn.classList.add('rm-shake');
    });
  });

  const positionKey='kotoba:roadmap-position:v1';
  document.querySelectorAll('a.rm-node[href]').forEach(link=>link.addEventListener('click',()=>{
    try{sessionStorage.setItem(positionKey,JSON.stringify({chapter:link.closest('[data-chapter]').dataset.chapter,y:window.scrollY}));history.replaceState({...history.state,kotobaRoadmapReturn:true},'');}catch(_){}
  }));
  function centerVertically(element) {
    const rect=element.getBoundingClientRect();
    window.scrollTo({left:0,top:Math.max(0,window.scrollY+rect.top-(window.innerHeight-rect.height)/2),behavior:'instant'});
  }
  function restorePosition(back) {
    const id=location.hash.startsWith('#chapter-')?location.hash.slice(9):'';
    let saved=null;try{saved=JSON.parse(sessionStorage.getItem(positionKey));}catch(_){}
    if(saved&&Number.isFinite(saved.y)&&saved.y>=0&&((id&&id===saved.chapter)||(back&&history.state?.kotobaRoadmapReturn))){window.scrollTo({left:0,top:saved.y,behavior:'instant'});return true;}
    const chapter=id&&document.getElementById('chapter-'+id);
    if(chapter){centerVertically(chapter);return true;}
    return false;
  }
  const returned=restorePosition(performance.getEntriesByType?.('navigation')[0]?.type==='back_forward');
  // Fragment scrolling and offline font layout can run after deferred scripts.
  // Finish restoration once layout is ready, unless the learner has interacted.
  if(returned){
    const returnHash=location.hash;let interacted=false;
    for(const event of ['wheel','touchstart','pointerdown','keydown'])window.addEventListener(event,()=>{interacted=true;},{once:true,passive:true});
    function settled(){if(!interacted&&location.hash===returnHash)restorePosition(true);}
    window.addEventListener('load',()=>window.requestAnimationFrame(settled),{once:true});
    document.fonts?.ready.then(()=>window.requestAnimationFrame(settled));
  }
  window.addEventListener('pageshow',e=>{if(e.persisted)restorePosition(true);});
  // A fresh course visit may focus the recommendation; returning keeps your place.
  var current = document.querySelector('.rm-current .rm-node') || document.querySelector('.rm-node.rm-unlocked');
  if (!returned && current && !location.hash && Number(document.getElementById('rm-path')?.dataset.completed)>0) {
    centerVertically(current);
  }

  // If the learner just completed a chapter and returned to the path,
  // celebrate the newly checked node once without blocking navigation.
  try {
    var justDone = sessionStorage.getItem('kotoba:roadmap-just-completed');
    if (justDone) {
      sessionStorage.removeItem('kotoba:roadmap-just-completed');
      say('Chapter complete — your path moved forward!');
    }
  } catch (e) {}

})();

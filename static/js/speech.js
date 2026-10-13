(function () {
  let current = null, owner = null, trigger = null;
  document.addEventListener('click', e=>{trigger=e.target.closest?.('button,a');},true);
  function clean(text) { return String(text || '').replace(/\s+/g,' ').trim(); }
  // A kanji alone is ambiguous to TTS. Use this card's kana, never a global
  // kanji substitution (生, for example, has different readings in words).
  function readingText(text, reading) {
    const parts=clean(reading).split('·');
    let kana=parts.find(x=>/[\u3041-\u3096\u30a1-\u30fa]/.test(x))||parts[0];
    if(!/[。！？!?]/.test(kana))kana=kana.split(/\s*[,，;；/／]\s*/)[0];
    kana=kana.replace(/[（(]([^）)]*)[）)]/g,(_,s)=>/^[\u3040-\u30ffー]+$/.test(s)?s:'')
      .replace(/[A-Za-z\u00c0-\u024f]+(?:[-'][A-Za-z\u00c0-\u024f]+)*/g,'')
      .replace(/\./g,'').trim();
    return /[\u3041-\u3096\u30a1-\u30fa]/.test(kana)?kana:clean(text);
  }
  function speakReading(text, reading, rate) { speak(readingText(text,reading),rate); }
  function readingChoices(reading) {
    return [...new Set(clean(reading).split(/[,，、;；/／]/).map(x=>readingText('',x)).filter(Boolean))];
  }
  function blocksText(blocks, fallback) {
    if(!Array.isArray(blocks)||!blocks.length)return clean(fallback);
    return blocks.map(line=>Array.isArray(line)?line.map(x=>typeof x==='string'?x:(x?.reading||x?.text||'')).join(''):'').join(' ');
  }
  function speak(text, rate) {
    text=clean(text); if (!text) return;
    stop();
    window.dispatchEvent(new Event('kotoba-audio-before-play'));
    owner=trigger?.isConnected?trigger:document.activeElement;
    if (window.KotobaLearn) KotobaLearn.action('audio');
    try {
      if (window.KotobaSpeechNative && typeof window.KotobaSpeechNative.speak === 'function') {
        window.KotobaSpeechNative.speak(text, Number(rate || 0.92));
        return;
      }
    } catch (_) {}
    if (!('speechSynthesis' in window)) return;
    speechSynthesis.cancel();
    const u=new SpeechSynthesisUtterance(text); u.lang='ja-JP'; u.rate=Number(rate || 0.92); u.pitch=1;
    const voices=speechSynthesis.getVoices();
    const ja=voices.find(v=>/^ja(-|_)/i.test(v.lang || ''));
    if (ja) u.voice=ja;
    current=u; speechSynthesis.speak(u);
  }
  function stop() {
    try { if (window.KotobaSpeechNative) window.KotobaSpeechNative.stop(); } catch (_) {}
    if ('speechSynthesis' in window) speechSynthesis.cancel(); current=null;
    owner=null;
    document.querySelectorAll('audio').forEach(audio=>{try{audio.pause();audio.currentTime=0;}catch(_){}});
  }
  function wire(root) {
    const selector='[data-speak]:not([data-speak-wired])',nodes=[...(root || document).querySelectorAll(selector)];
    if(root?.matches?.(selector))nodes.push(root);
    nodes.forEach(btn=>{
      btn.dataset.speakWired='1';
      btn.addEventListener('click',(ev)=>{ev.preventDefault();ev.stopPropagation();speakReading(btn.dataset.speak, btn.dataset.reading, btn.dataset.rate);});
    });
  }
  window.KotobaSpeech={speak,speakReading,readingText,readingChoices,blocksText,stop,wire};
  window.addEventListener('pagehide',()=>{stop();mo.disconnect();});
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')stop();});
  window.addEventListener('kotoba-audio-before-capture',stop);
  document.addEventListener('click',e=>{
    if(e.target.closest?.('a[href]:not([href^="#"])'))stop();
    const button=e.target.closest?.('button');
    if(button&&/(?:^|[-_])(next|prev|previous|again|back|close|stop)(?:$|[-_])/.test(button.id))stop();
  },true);
  document.addEventListener('DOMContentLoaded',()=>wire(document));
  const mo=new MutationObserver(m=>{
    if(owner){let hidden=!owner.isConnected;for(let el=owner;el;el=el.parentElement){if(el.hidden||el.getAttribute('aria-hidden')==='true'||el.style.display==='none')hidden=true;}if(hidden)stop();}
    for(const x of m){for(const n of x.addedNodes){if(n.nodeType===1)wire(n);}}
  });
  document.addEventListener('DOMContentLoaded',()=>{if(document.body)mo.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden','aria-hidden','style','class']});});
  window.addEventListener('pageshow',e=>{if(e.persisted&&document.body)mo.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden','aria-hidden','style','class']});});
})();

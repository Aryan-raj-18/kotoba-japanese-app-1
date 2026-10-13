/* Kotoba stable Liquid Glass controller — Build 47.
   Previously the SVG displacement map (from liquid-glass-react, MIT) was
   injected into a fixed/sticky DOM layer, causing rectangular artifacts
   in desktop Chromium and Android WebView. Its license/source are retained
   for reference, but active glass now uses native backdrop composition.
   No extra painting surface, filter-region overflow, wallpaper clone, or animation loop. */
(function () {
  'use strict';
  var KEY='kotoba:liquid-glass';
  var root=document.documentElement;
  var toggle=document.getElementById('liquid-glass-switch');
  var hint=document.getElementById('liquid-glass-hint');
  var supports=!!(window.CSS && window.CSS.supports &&
    (window.CSS.supports('backdrop-filter','blur(1px)') || window.CSS.supports('-webkit-backdrop-filter','blur(1px)')));
  var media=window.matchMedia;
  var reduceTransparency=!!(media && media('(prefers-reduced-transparency: reduce)').matches);
  var qualityLite=!!((navigator.deviceMemory && navigator.deviceMemory<=3)||!supports||reduceTransparency);
  if(qualityLite) root.setAttribute('data-glass-quality','lite');
  function enabled(){try{return localStorage.getItem(KEY)!=='off';}catch(_){return true;}}
  function apply(on){root.setAttribute('data-glass',on?'on':'off');
    if(toggle)toggle.setAttribute('aria-checked',String(!!on));
    if(hint)hint.textContent=on?'On · Glass finish throughout the app':'Off · Solid theme surfaces';}
  apply(enabled());
  if(toggle)toggle.addEventListener('click',function(){
    var next=root.getAttribute('data-glass')!=='on';
    try{localStorage.setItem(KEY,next?'on':'off');}catch(_){}
    apply(next);
  });
  if(window.addEventListener)window.addEventListener('storage',function(event){
    if(event.key===KEY||event.key===null)apply(enabled());
  });
  window.KotobaLiquidGlass={apply:apply,supported:supports,
    activeSurfaces:function(){return 0;}};
})();

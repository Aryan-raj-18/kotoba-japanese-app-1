/* Keep the page under a sheet still, including Android WebView touch scroll.
   One owner handles nested overlays so closing one cannot unlock another. */
(function () {
  'use strict';
  var root = document.documentElement;
  var locked = false, savedX = 0, savedY = 0;
  var selector = '.modal-overlay,.settings-panel,.onboarding-overlay,.voice-search-overlay,' +
    '.wallpaper-crop-overlay,.practice-exit-overlay,.japan-passport-modal,.japan-drawer.open,.japan-map-wrap.is-expanded';
  function visible(node) {
    for (var p = node; p && p.nodeType === 1; p = p.parentElement) {
      if (p.hidden || p.getAttribute('aria-hidden') === 'true' || p.style.display === 'none') return false;
    }
    return true;
  }
  function refresh() {
    if (!window.document || !window.document.body) return;
    var active = Array.from(document.querySelectorAll(selector)).some(visible);
    if (active === locked) return;
    locked = active;
    if (active) {
      savedX = window.scrollX || 0;
      savedY = window.scrollY || 0;
      root.style.setProperty('--kotoba-scroll-top', -savedY + 'px');
      root.classList.add('kotoba-scroll-locked');
    } else {
      var behavior = root.style.getPropertyValue('scroll-behavior');
      var priority = root.style.getPropertyPriority('scroll-behavior');
      root.style.setProperty('scroll-behavior', 'auto', 'important');
      root.classList.remove('kotoba-scroll-locked');
      root.style.removeProperty('--kotoba-scroll-top');
      window.scrollTo(savedX, savedY);
      if (behavior) root.style.setProperty('scroll-behavior', behavior, priority);
      else root.style.removeProperty('scroll-behavior');
    }
  }
  var observer = new MutationObserver(refresh);
  function observe() { observer.observe(document.body, {
    subtree: true, childList: true, attributes: true,
    attributeFilter: ['hidden', 'aria-hidden', 'class', 'style']
  }); }
  observe();
  window.addEventListener('pagehide', function () { observer.disconnect(); });
  window.addEventListener('pageshow', function () { observe(); refresh(); });
  window.KotobaScrollLock = { refresh: refresh };
  refresh();
})();

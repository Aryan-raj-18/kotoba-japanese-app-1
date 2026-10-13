(function () {
  'use strict';
  const key = 'kotoba:home-journey-position:v1';
  document.querySelectorAll('a[data-home-journey]').forEach(link => link.addEventListener('click', () => {
    try {
      sessionStorage.setItem(key, JSON.stringify({y: window.scrollY}));
      history.replaceState({...history.state, kotobaHomeJourneyReturn: true}, '');
    } catch (_) {}
  }));
  function restore(back) {
    if (location.hash !== '#home-journey' && !(back && history.state?.kotobaHomeJourneyReturn)) return false;
    let saved = null; try { saved = JSON.parse(sessionStorage.getItem(key)); } catch (_) {}
    const heading = document.getElementById('home-journey');
    const y = saved && Number.isFinite(saved.y) && saved.y >= 0 ? saved.y :
      heading ? window.scrollY + heading.getBoundingClientRect().top - 110 : 0;
    window.scrollTo({left: 0, top: Math.max(0, y), behavior: 'instant'});
    return true;
  }
  const returned = restore(window.performance.getEntriesByType?.('navigation')[0]?.type === 'back_forward');
  if (returned) {
    const hash = location.hash; let interacted = false;
    for (const event of ['wheel', 'touchstart', 'pointerdown', 'keydown'])
      window.addEventListener(event, () => { interacted = true; }, {once: true, passive: true});
    function settled() { if (!interacted && location.hash === hash) restore(true); }
    window.addEventListener('load', () => window.requestAnimationFrame(settled), {once: true});
    document.fonts?.ready.then(() => window.requestAnimationFrame(settled));
  }
  window.addEventListener('pageshow', event => { if (event.persisted) restore(true); });
})();

(function () {
  'use strict';
  var KEY = 'kotoba:onboarding:v3';
  var GOAL_KEY = 'kotoba:daily-goal-minutes';
  var goal = 10;
  try { goal = Number(localStorage.getItem(GOAL_KEY)) || 10; } catch (e) {}
  var goalPill = document.getElementById('home-goal-pill');
  if (goalPill) goalPill.textContent = 'Daily goal · ' + goal + ' min';

  if (goalPill) goalPill.addEventListener('click', function (event) {
    event.stopPropagation();
    var settings=document.getElementById('settings-btn');
    if(settings && settings.getAttribute('aria-expanded') !== 'true') settings.click();
    var chips=document.getElementById('settings-goal-chips');
    if(chips) { chips.scrollIntoView({block:'center',behavior:'auto'}); chips.querySelector('button')?.focus({preventScroll:true}); }
  });

  var overlay = document.getElementById('onboarding-overlay');
  if (!overlay) return;
  try {
    if (localStorage.getItem(KEY)) return;
  } catch (e) {}


  function saveSetup() {
    try {
      localStorage.setItem(KEY, '1');
    } catch (e) {}
  }

  document.querySelectorAll('.onboarding-levels [data-start]').forEach(function (button) {
    button.addEventListener('click', function () {
      saveSetup();
      var href = button.getAttribute('data-start');
      var match = /^\/roadmap\/([^/?#]+)/.exec(href || '');
      var roadmapStart = button.getAttribute('data-roadmap-start') || (match ? decodeURIComponent(match[1]) : '');
      if (!roadmapStart) {
        window.location.href = href;
        return;
      }
      fetch('/api/roadmap/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chapter_id: roadmapStart })
      }).catch(function () {}).finally(function () {
        window.location.href = href;
      });
    });
  });

  var skip = document.getElementById('onboarding-skip');
  if (skip) skip.addEventListener('click', function () {
    saveSetup();
    overlay.hidden = true;
    document.body.classList.remove('onboarding-open');
  });

  overlay.addEventListener('click', function (event) {
    if (event.target === overlay) {
      saveSetup();
      overlay.hidden = true;
      document.body.classList.remove('onboarding-open');
    }
  });

  function showOnboarding() {
    // Record the first appearance, including leaving for the placement test
    // or closing the app before choosing a starting point.
    saveSetup();
    document.body.classList.add('onboarding-open');
    overlay.hidden = false;
  }
  if (document.body.classList.contains('intro-open')) {
    window.addEventListener('kotoba:intro:done', function () {
      setTimeout(showOnboarding, 180);
    }, { once: true });
  } else {
    setTimeout(showOnboarding, 250);
  }
})();

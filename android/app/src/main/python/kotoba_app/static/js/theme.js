/* =====================================================================
   Kotoba — theme switching
   ---------------------------------------------------------------------
   The actual palettes live in style.css, keyed off <html data-theme>.
   This file only decides *which* key is set, remembers the choice, and
   wires up the settings menu in the header.

   A tiny inline copy of the "apply saved theme" step runs in base.html's
   <head>, before the stylesheet paints, so switching to a dark theme
   doesn't flash a screen of white paper on every navigation.
   ================================================================== */

(function () {
  'use strict';

  var KEY='kotoba:theme',catalog=window.KotobaThemeCatalog;
  var THEMES=catalog.themes,resolve=catalog.resolve,read=catalog.read;
  function save(id){try{localStorage.setItem(KEY,catalog.migrate(id));}catch(_){}}
  function apply(id,animate){
    id=catalog.migrate(id);const resolved=resolve(id),theme=THEMES.find(t=>t.id===resolved),root=document.documentElement;
    root.setAttribute('data-theme',resolved);root.setAttribute('data-theme-choice',id);
    const meta=document.querySelector('meta[name="theme-color"]');if(meta)meta.content=theme.paper;
    document.querySelectorAll('.theme-opt').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.theme===id)));
    const system=document.getElementById('theme-system-switch');if(system)system.setAttribute('aria-checked',String(id==='auto'));
    if(window.KotobaThemeIcons)window.KotobaThemeIcons.refresh();
    if(window.KotobaDisplayNative)window.KotobaDisplayNative.setTheme(theme.paper,theme.dark);
    root.classList.remove('theme-switched');clearTimeout(apply.timer);
    if(animate&&!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)){
      void root.offsetWidth;root.classList.add('theme-switched');
      clearTimeout(apply.timer);apply.timer=setTimeout(()=>root.classList.remove('theme-switched'),theme.duration+50);
    }
    window.dispatchEvent(new CustomEvent('kotoba-theme-change',{detail:resolved}));
  }
  if(window.matchMedia){const mq=window.matchMedia('(prefers-color-scheme: dark)');const change=()=>{if(read()==='auto')apply('auto');};if(mq.addEventListener)mq.addEventListener('change',change);else if(mq.addListener)mq.addListener(change);}

  // Two intentional appearances only. Keep familiar Light/Dark buttons.
  function buildThemeOptions(container) {
    THEMES.forEach(function (t) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'theme-opt';
      btn.dataset.theme = t.id;
      btn.setAttribute('aria-pressed', 'false');
      btn.innerHTML =
        '<span class="theme-swatch theme-preview" aria-hidden="true"><i class="preview-sun"></i><i class="preview-mountain"></i><i class="preview-card"><b></b><em></em></i><i class="preview-nav"></i></span>' +
        '<span><span class="theme-opt-name"></span><span class="theme-opt-jp"></span></span>';
      btn.querySelector('.theme-opt-name').textContent = t.name;
      btn.querySelector('.theme-opt-jp').textContent = t.jp + ' · ' + t.description;
      btn.querySelector('.theme-swatch').style.setProperty('--sw-a', t.paper);
      btn.querySelector('.theme-swatch').style.setProperty('--sw-b', t.accent);
      btn.querySelector('.theme-swatch').style.setProperty('--preview-ink', t.ink);
      btn.addEventListener('click', function () {
        save(t.id); apply(t.id, true);
        if (window.Sfx) Sfx.tap();
      });
      container.appendChild(btn);
    });
  }

  function wireSwitch(el, isOn, setter) {
    if (!el) return;
    el.setAttribute('aria-checked', String(isOn()));
    el.addEventListener('click', function () {
      var next = el.getAttribute('aria-checked') !== 'true';
      setter(next);
      el.setAttribute('aria-checked', String(next));
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    apply(read() || 'auto');

    var optionsEl = document.getElementById('theme-options');
    if (optionsEl) {
      buildThemeOptions(optionsEl);
      apply(read() || 'auto'); // re-run so the new buttons get their pressed state
    }

    if (window.Sfx) {
      wireSwitch(document.getElementById('sound-switch'), Sfx.isSoundOn, Sfx.setSound);
      wireSwitch(document.getElementById('haptics-switch'), Sfx.isHapticsOn, Sfx.setHaptics);
    }

    const system=document.getElementById('theme-system-switch');
    system?.addEventListener('click',()=>{const id=read()==='auto'?resolve('auto'):'auto';save(id);apply(id,true);});
    const status=document.getElementById('status-bar-switch');
    if(status&&window.KotobaDisplayNative){
      document.getElementById('status-bar-row').hidden=false;document.getElementById('status-bar-hint').hidden=false;
      status.setAttribute('aria-checked',String(window.KotobaDisplayNative.getHideStatusBar()));
      status.addEventListener('click',()=>{const hidden=status.getAttribute('aria-checked')!=='true';window.KotobaDisplayNative.setHideStatusBar(hidden);status.setAttribute('aria-checked',String(hidden));});
    }
    // ---- open / close the panel ----
    var btn = document.getElementById('settings-btn');
    var panel = document.getElementById('settings-panel');
    if (!btn || !panel) return;

    // Below 560px the panel becomes a fixed bottom sheet (see style.css).
    // But its normal home — inside .settings-wrap, inside the immersive
    // shell's .site-header — sits under an ancestor with backdrop-filter,
    // and a backdrop-filter/filter/transform on any ancestor makes that
    // ancestor the containing block for position:fixed descendants
    // instead of the viewport. On phones that pinned the "fixed" sheet
    // to the small header bar rather than the screen, so only a sliver
    // of it was ever visible. Moving the panel out to a direct child of
    // <body> right before it opens keeps it a true viewport-fixed sheet
    // on mobile, and moving it back restores the normal dropdown
    // (position:absolute against .settings-wrap) on desktop.
    var panelHome = panel.parentNode;
    var panelHomeNext = panel.nextSibling;
    var mqMobile = window.matchMedia('(max-width: 560px)');

    function placePanel() {
      if (mqMobile.matches) {
        if (panel.parentNode !== document.body) document.body.appendChild(panel);
      } else if (panel.parentNode !== panelHome) {
        panelHome.insertBefore(panel, panelHomeNext);
      }
    }

    function close() {
      panel.hidden = true;
      btn.setAttribute('aria-expanded', 'false');
    }
    function open() {
      placePanel();
      panel.hidden = false;
      btn.setAttribute('aria-expanded', 'true');
    }

    // If the viewport crosses the breakpoint while the panel is open
    // (e.g. rotating the phone, or resizing a desktop window), just
    // close it rather than leaving it mis-anchored mid-transition.
    var onMqChange = function () { if (!panel.hidden) close(); };
    if (mqMobile.addEventListener) mqMobile.addEventListener('change', onMqChange);
    else if (mqMobile.addListener) mqMobile.addListener(onMqChange);

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      if (panel.hidden) { open(); if (window.Sfx) Sfx.tap(); } else { close(); }
    });
    panel.addEventListener('click', function (e) { e.stopPropagation(); });
    document.addEventListener('click', function () { if (!panel.hidden) close(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !panel.hidden) { close(); btn.focus(); }
    });
  });

  window.KotobaTheme = { apply: apply, resolve: resolve, themes: THEMES };
})();

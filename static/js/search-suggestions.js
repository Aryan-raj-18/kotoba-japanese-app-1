/* Prefix suggestions from the offline dictionary; precise full search stays available. */
(function () {
  'use strict';
  var cache = new Map();
  document.querySelectorAll('form.header-search input[name="q"], form.hero-search input[name="q"]').forEach(function (input, n) {
    var form = input.form, panel = document.createElement('div'), status = document.createElement('p');
    var timer, controller, token = 0, active = -1, links = [], composing = false;
    panel.className = 'search-suggestions'; panel.id = 'search-suggestions-' + n;
    panel.setAttribute('role', 'listbox'); panel.setAttribute('aria-label', 'Suggested words'); panel.hidden = true;
    status.className = 'search-suggestion-status'; status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite'); form.append(panel, status); form.classList.add('has-search-suggestions');
    input.setAttribute('role', 'combobox'); input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-controls', panel.id); input.setAttribute('aria-expanded', 'false');
    if (!input.hasAttribute('aria-label')) input.setAttribute('aria-label', 'Search Japanese, English or romaji');
    function close() {
      clearTimeout(timer); token++; if (controller) controller.abort();
      panel.hidden = true; active = -1; input.setAttribute('aria-expanded', 'false');
      input.removeAttribute('aria-activedescendant'); status.textContent = '';
    }
    function render(rows, q) {
      panel.replaceChildren(); links = []; active = -1;
      rows.forEach(function (row, i) {
        if (!/^\/(?:search\/entry\/[a-f0-9]+|[a-z][a-z0-9_/-]*(?:\?[^\s]*)?(?:#[^\s]*)?)$/.test(row.href)) return;
        var link = document.createElement('a'); link.className = 'search-suggestion';
        link.href = row.href + (row.href.indexOf('/search/entry/') === 0 ? '?q=' + encodeURIComponent(q) : '');
        link.id = panel.id + '-option-' + i; link.setAttribute('role', 'option'); link.setAttribute('aria-selected', 'false');
        var word = document.createElement('strong'), reading = document.createElement('span'), meaning = document.createElement('small');
        word.textContent = row.word; reading.textContent = [row.reading, row.romaji].filter(Boolean).join(' · ');
        meaning.textContent = row.meaning; link.append(word, reading, meaning); panel.append(link); links.push(link);
      });
      panel.hidden = !links.length; input.setAttribute('aria-expanded', String(!!links.length));
      var rect = form.getBoundingClientRect(), nav = document.querySelector('.kotoba-bottom-nav');
      var navRect = nav && nav.getBoundingClientRect();
      var bottom = navRect && navRect.height > 0 ? Math.min(innerHeight, navRect.top) : innerHeight;
      var below = bottom - rect.bottom, above = rect.top;
      var opensAbove = below < 180 && above > below;
      panel.classList.toggle('opens-above', opensAbove);
      panel.style.maxHeight = Math.min(380, Math.max(112, (opensAbove ? above : below) - 16)) + 'px';
      input.removeAttribute('aria-activedescendant');
      status.textContent = links.length ? links.length + ' suggested words. Use arrow keys or tap a word.' : '';
    }
    function eligible(q) { return q.length <= 100 && (/[^\x00-\x7f]/.test(q) ? q.length >= 1 : q.length >= 2); }
    async function request(q, id) {
      try {
        var rows = cache.get(q);
        if (!rows) {
          controller = new AbortController();
          var response = await fetch('/api/search/suggest?q=' + encodeURIComponent(q), {signal: controller.signal});
          if (!response.ok) throw Error('suggestions'); rows = await response.json();
          if (!Array.isArray(rows)) throw Error('suggestions');
          cache.set(q, rows); if (cache.size > 64) cache.delete(cache.keys().next().value);
        }
        if (id === token && document.activeElement === input && input.value.trim() === q) render(rows, q);
      } catch (_) { if (id === token) close(); }
    }
    function update() {
      close(); var q = input.value.trim(); if (composing || !eligible(q)) return;
      var id = token; timer = setTimeout(function () { request(q, id); }, 150);
    }
    input.addEventListener('input', update); input.addEventListener('focus', update);
    input.addEventListener('compositionstart', function () { composing = true; close(); });
    input.addEventListener('compositionend', function () { composing = false; update(); });
    input.addEventListener('keydown', function (event) {
      if (event.isComposing || composing) return;
      if (event.key === 'Escape') { close(); return; }
      if (panel.hidden) return;
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault(); active = (active + (event.key === 'ArrowDown' ? 1 : -1) + links.length) % links.length;
        links.forEach(function (link, i) { link.setAttribute('aria-selected', String(i === active)); });
        input.setAttribute('aria-activedescendant', links[active].id); links[active].scrollIntoView?.({block: 'nearest'});
      } else if (event.key === 'Enter' && active >= 0) { event.preventDefault(); window.location.href = links[active].href; }
    });
    form.addEventListener('focusout', function (event) { if (!form.contains(event.relatedTarget)) close(); });
    form.addEventListener('submit', close);
    document.addEventListener('pointerdown', function (event) { if (!form.contains(event.target)) close(); });
    window.addEventListener('pagehide', close); window.addEventListener('kotoba-voice-search-start', close);
  });
})();

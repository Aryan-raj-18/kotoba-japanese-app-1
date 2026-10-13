/* Shared spelling rules for typed and spoken local filters. */
(function () {
  'use strict';
  function normalize(value) {
    return String(value || '').normalize('NFKC').toLowerCase()
      .replace(/[\u30a1-\u30f6]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0x60); })
      .replace(/[\u00c0-\u024f\u1e00-\u1eff]/g, function (c) { return c.normalize('NFD').replace(/[\u0300-\u036f]/g, ''); })
      .replace(/['’]/g, '').replace(/[\s.,!?;:，。！？、・「」『』（）()\[\]{}"“”/\\_\-]+/g, ' ').trim();
  }
  var cache = new Map();
  function includes(hay, query) {
    if (/[a-z]/.test(query)) {
      var escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      return new RegExp('(^|[^a-z0-9])' + escaped + '($|[^a-z0-9])').test(hay);
    }
    return hay.replace(/\s/g, '').includes(query.replace(/\s/g, ''));
  }
  function matches(text, query) {
    var hay = cache.get(text);
    if (hay === undefined) { hay = normalize(text); cache.set(text, hay); }
    var q = normalize(query);
    return !q || includes(hay, q) || q.split(/\s+/).every(function (part) { return includes(hay, part); });
  }
  window.KotobaSearchMatch = {normalize: normalize, matches: matches};
})();

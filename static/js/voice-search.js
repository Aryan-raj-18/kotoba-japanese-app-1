(function () {
  'use strict';
  var LANG_KEY = 'kotoba:voice-search-language';
  var activeInput = null, globalMode = false, recognition = null;
  var listening = false, session = 0, timer = null, finishTimer = null, returnFocus = null;
  var overlay = document.getElementById('voice-search-overlay');
  if (!overlay) return;
  var statusEl = document.getElementById('voice-search-status');
  var transcriptEl = document.getElementById('voice-search-transcript');
  var retryBtn = document.getElementById('voice-search-retry');
  var useBtn = document.getElementById('voice-search-use');
  var stopBtn = document.getElementById('voice-search-stop');
  var alternativesEl = document.getElementById('voice-search-alternatives');
  var everywhere = document.getElementById('voice-search-everywhere');
  function lang() {
    var value;
    try { value = localStorage.getItem(LANG_KEY); } catch (e) {}
    return ['ja-JP', 'en-US', 'auto'].indexOf(value) >= 0 ? value : (/^ja/i.test(navigator.language) ? 'ja-JP' : 'en-US');
  }
  function setLang(value) {
    try { localStorage.setItem(LANG_KEY, value); } catch (e) {}
    document.querySelectorAll('[data-voice-lang]').forEach(function (button) {
      button.classList.toggle('active', button.dataset.voiceLang === value);
      button.setAttribute('aria-pressed', String(button.dataset.voiceLang === value));
    });
  }
  function status(text) { statusEl.textContent = text; }
  function markListening(value) {
    listening = value;
    stopBtn.hidden = !value;
    overlay.classList.toggle('is-listening', value);
    document.querySelectorAll('.voice-inline-btn,.voice-search-global-btn').forEach(function (b) { b.classList.toggle('listening', value); });
  }
  function updateText(text) {
    transcriptEl.value = text;
    useBtn.disabled = !text.trim();
    everywhere.href = '/search?q=' + encodeURIComponent(text.trim());
    everywhere.hidden = globalMode || !text.trim();
  }
  function current(id) { return String(id) === String(session) && !overlay.hidden; }
  function clearTimers() { clearTimeout(timer); clearTimeout(finishTimer); timer = finishTimer = null; }
  function stop() {
    session += 1; clearTimers(); markListening(false);
    var previous = recognition; recognition = null;
    if (previous) { previous.onresult = previous.onerror = previous.onend = null; try { previous.abort(); } catch (e) {} }
    try { if (window.KotobaVoiceRecognitionNative) window.KotobaVoiceRecognitionNative.stop(); } catch (e) {}
  }
  function hide() {
    stop(); overlay.hidden = true; document.body.classList.remove('voice-search-open');
    if (returnFocus && returnFocus.isConnected) returnFocus.focus();
  }
  function alternatives(items) {
    alternativesEl.textContent = '';
    var seen = [transcriptEl.value.trim()];
    (items || []).slice(0, 5).forEach(function (text) {
      text = String(text || '').trim();
      if (!text || seen.indexOf(text) !== -1) return;
      seen.push(text);
      var button = document.createElement('button'); button.type = 'button'; button.textContent = text;
      button.addEventListener('click', function () { stop(); updateText(text); alternativesEl.hidden = true; status('Ready to search. You can edit the words above.'); });
      alternativesEl.appendChild(button);
    });
    alternativesEl.hidden = !alternativesEl.children.length;
  }
  function review(text, choices) {
    clearTimers(); markListening(false);
    updateText(String(text || '').trim()); alternatives(choices);
    retryBtn.hidden = false;
    status(transcriptEl.value ? 'Check the complete phrase, then tap Search.' : 'No words heard. Try again or type above.');
  }
  function fail(message) {
    clearTimers(); markListening(false); retryBtn.hidden = false;
    status(message || 'Could not recognize that. Try again or type above.');
  }
  function finish() {
    if (!listening) return;
    clearTimeout(timer); stopBtn.hidden = true; status('Finishing…');
    try {
      if (recognition) recognition.stop();
      else if (window.KotobaVoiceRecognitionNative && typeof window.KotobaVoiceRecognitionNative.finish === 'function') window.KotobaVoiceRecognitionNative.finish();
      else { var text = transcriptEl.value; stop(); review(text); return; }
    } catch (e) { var text = transcriptEl.value; stop(); review(text); return; }
    var id = session;
    finishTimer = setTimeout(function () { if (current(id)) { var text = transcriptEl.value; stop(); review(text); } }, 3000);
  }
  function start(input, options) {
    window.KotobaSpeech?.stop();
    window.dispatchEvent?.(new Event('kotoba-voice-search-start'));
    var wasOpen = !overlay.hidden;
    stop(); activeInput = input || null; globalMode = !!(options && options.global) || !!(input && input.form && input.name === 'q');
    if (!wasOpen) returnFocus = document.activeElement;
    overlay.hidden = false; document.body.classList.add('voice-search-open');
    updateText(''); alternatives([]); retryBtn.hidden = true; useBtn.textContent = globalMode ? 'Search' : 'Use in this section';
    setLang(lang()); markListening(true); status('Listening… Speak a word or a full sentence.');
    document.getElementById('voice-search-close').focus();
    var id = session, language = lang(), native = window.KotobaVoiceRecognitionNative;
    timer = setTimeout(function () { if (current(id)) finish(); }, 30000);
    if (native && typeof native.start === 'function') {
      try {
        if (typeof native.startSession === 'function') native.startSession(language === 'auto' ? '' : language, String(id));
        else native.start(language === 'auto' ? '' : language);
        return;
      } catch (e) {}
    }
    var Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Rec) { fail('Voice recognition is unavailable here. You can type above.'); return; }
    try {
      var rec = new Rec(); recognition = rec;
      rec.lang = language === 'auto' ? (navigator.language || 'en-US') : language;
      rec.interimResults = true; rec.continuous = true; rec.maxAlternatives = 5;
      rec.onresult = function (event) {
        if (!current(id) || !listening) return;
        // results is cumulative. Rebuild the WHOLE utterance, not only resultIndex.
        var texts = [], choices = [''];
        for (var i = 0; i < event.results.length; i++) {
          var result = event.results[i]; texts.push(result[0].transcript.trim());
          var next = [];
          choices.forEach(function (prefix) {
            for (var j = 0; j < Math.min(result.length, 5); j++) next.push((prefix + ' ' + result[j].transcript).trim());
          });
          choices = next.slice(0, 5);
        }
        updateText(texts.join(' ')); alternatives(choices);
      };
      rec.onerror = function (event) {
        if (!current(id) || !listening || event.error === 'aborted') return;
        var text = transcriptEl.value; stop(); updateText(text);
        fail(event.error === 'not-allowed' ? 'Microphone permission is needed. Allow it, or type above.' : 'Recognition stopped. Check the words above or try again.');
      };
      rec.onend = function () {
        if (!current(id) || !listening) return;
        recognition = null;
        var choices = Array.prototype.map.call(alternativesEl.children, function (b) { return b.textContent; });
        review(transcriptEl.value, choices);
      };
      rec.start();
    } catch (e) { stop(); fail('Could not start voice recognition. Try again or type above.'); }
  }
  function useText() {
    var text = transcriptEl.value.trim(), input = activeInput, all = globalMode;
    if (!text) return;
    hide();
    if (all) { window.location.href = '/search?q=' + encodeURIComponent(text); return; }
    if (input) {
      input.value = text; input.dispatchEvent(new Event('input', {bubbles: true}));
      input.dispatchEvent(new Event('change', {bubbles: true})); input.focus();
    }
  }
  function nativeCurrent(id) { return !overlay.hidden && listening && (id === undefined || current(id)); }
  window.KotobaVoiceSearch = {
    start: start, stop: stop,
    _nativeStatus: function (s, id) { if (nativeCurrent(id)) status(s === 'processing' ? 'Finishing…' : 'Listening… Speak a word or a full sentence.'); },
    _nativePartial: function (text, id) { if (nativeCurrent(id) && text) updateText(text); },
    _nativeResult: function (text, id) { if (nativeCurrent(id)) review(text); },
    _nativeResults: function (json, id) { if (!nativeCurrent(id)) return; try { var choices = JSON.parse(json); review(choices[0], choices); } catch (e) { fail('Could not read the result. Try again.'); } },
    _nativeError: function (message, id) { if (nativeCurrent(id)) fail(message); }
  };
  function addButton(input) {
    if (!input || input.dataset.voiceReady === '1') return;
    input.dataset.voiceReady = '1'; var parent = input.parentElement;
    if (!parent.classList.contains('voice-field')) {
      var wrap = document.createElement('span'); wrap.className = 'voice-field';
      parent.insertBefore(wrap, input); wrap.appendChild(input); parent = wrap;
    }
    var button = document.createElement('button'); button.type = 'button'; button.className = 'voice-inline-btn';
    button.setAttribute('aria-label', 'Search by voice'); button.title = 'Voice search'; button.textContent = '🎙';
    parent.appendChild(button); button.addEventListener('click', function () { start(input, {}); });
  }
  document.querySelectorAll('.filter-input, form.header-search input[name="q"], form.hero-search input[name="q"], input[type="search"][data-voice-search]').forEach(addButton);
  var global = document.getElementById('voice-search-global');
  if (global) global.addEventListener('click', function () { start(null, {global: true}); });
  document.getElementById('voice-search-close').addEventListener('click', hide);
  retryBtn.addEventListener('click', function () { start(activeInput, {global: globalMode}); });
  stopBtn.addEventListener('click', finish); useBtn.addEventListener('click', useText);
  transcriptEl.addEventListener('input', function () { if (listening) stop(); updateText(transcriptEl.value); alternativesEl.hidden = true; retryBtn.hidden = false; status('Ready to search.'); });
  document.querySelectorAll('[data-voice-lang]').forEach(function (b) {
    b.addEventListener('click', function () { setLang(b.dataset.voiceLang); start(activeInput, {global: globalMode}); });
  });
  overlay.addEventListener('click', function (event) { if (event.target === overlay) hide(); });
  overlay.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') { event.preventDefault(); hide(); }
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') { event.preventDefault(); useText(); }
    if (event.key === 'Tab') {
      var controls = Array.prototype.filter.call(overlay.querySelectorAll('button,textarea,a[href]'), function (el) { return !el.disabled && el.offsetParent !== null; });
      var first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  window.addEventListener('pagehide', stop);
  window.addEventListener('kotoba-audio-before-play',stop);
  document.addEventListener?.('visibilitychange',function(){if(document.visibilityState==='hidden')stop();});
})();

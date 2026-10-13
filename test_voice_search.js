/* Behavior checks for complete utterances, editing, and stale callbacks.
   Run with node test_voice_search.js; no browser/microphone is required. */
'use strict';
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const {test} = require('node:test');

function environment(native) {
  class Element {
    constructor() {
      this.value = ''; this.hidden = true; this.disabled = false;
      this.children = []; this.dataset = {}; this.listeners = {};
      this.isConnected = true; this.offsetParent = {}; this.attributes = {};
      const classes = new Set();
      this.classList = {add: (...v) => v.forEach(x => classes.add(x)), remove: (...v) => v.forEach(x => classes.delete(x)),
        contains: v => classes.has(v), toggle: (v, force) => {if (force === undefined) force = !classes.has(v); if (force) classes.add(v); else classes.delete(v);}};
    }
    set textContent(value) { this.text = value; this.children = []; }
    get textContent() { return this.text || ''; }
    setAttribute(key, value) { this.attributes[key] = value; }
    addEventListener(type, fn) { this.listeners[type] = fn; }
    appendChild(child) { this.children.push(child); child.parentElement = this; }
    insertBefore(child) { this.appendChild(child); }
    dispatchEvent(event) { if (this.listeners[event.type]) this.listeners[event.type](event); }
    fire(type, extra = {}) { this.dispatchEvent(Object.assign({type, target: this}, extra)); }
    focus() { doc.activeElement = this; }
    querySelectorAll() { return this.children; }
  }
  const nodes = new Map(), timers = new Map(), storage = new Map(), recordings = [];
  const doc = {body: new Element(), activeElement: new Element(),
    getElementById: id => {if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id);},
    createElement: () => new Element(), querySelectorAll: () => []};
  const win = {location: {href: '/original'}, addEventListener: () => {}};
  if (native) win.KotobaVoiceRecognitionNative = native;
  else win.SpeechRecognition = class {
    constructor() {recordings.push(this);}
    start() {this.started = true;}
    stop() {this.finished = true;}
    abort() {this.aborted = true;}
  };
  let timerId = 0;
  const context = {window: win, document: doc, navigator: {language: 'en-US'},
    localStorage: {getItem: k => storage.get(k), setItem: (k, v) => storage.set(k, v)},
    setTimeout: fn => {timers.set(++timerId, fn); return timerId;}, clearTimeout: id => timers.delete(id),
    Event: class {constructor(type) {this.type = type;}}};
  vm.runInNewContext(fs.readFileSync(__dirname + '/static/js/voice-search.js', 'utf8'), context);
  return {win, doc, get: doc.getElementById, recordings, timers, Element};
}

function result(...phrases) {
  return {results: phrases.map(text => {const r = [{transcript: text}]; r.isFinal = true; return r;})};
}

test('Browser speech preserves every segment and waits for user Search', () => {
  const e = environment();
  e.win.KotobaVoiceSearch.start(null, {global: true});
  const rec = e.recordings[0];
  rec.onresult(result('Where are'));
  rec.onresult(result('Where are', 'you from?'));
  rec.onend();
  assert.equal(e.get('voice-search-transcript').value, 'Where are you from?');
  assert.equal(e.win.location.href, '/original');
  e.get('voice-search-use').fire('click');
  assert.equal(e.win.location.href, '/search?q=Where%20are%20you%20from%3F');
});

test('Closing or restarting ignores a late result from the old recording', () => {
  const e = environment();
  e.win.KotobaVoiceSearch.start(null, {global: true});
  const stale = e.recordings[0].onresult;
  e.get('voice-search-close').fire('click');
  stale(result('wrong old recording'));
  assert.equal(e.win.location.href, '/original');
  e.win.KotobaVoiceSearch.start(null, {global: true});
  stale(result('wrong old recording'));
  e.recordings[1].onresult(result('water'));
  assert.equal(e.get('voice-search-transcript').value, 'water');
});

test('Correcting the transcript stops speech from overwriting the edit', () => {
  const e = environment(); e.win.KotobaVoiceSearch.start(null, {global: true});
  const stale = e.recordings[0].onresult;
  stale(result('understand'));
  e.get('voice-search-transcript').value = 'stand';
  e.get('voice-search-transcript').fire('input');
  stale(result('wrong later transcript'));
  assert.equal(e.get('voice-search-transcript').value, 'stand');
  e.get('voice-search-use').fire('click');
  assert.equal(e.win.location.href, '/search?q=stand');
});

test('Native Done speaking requests the final result instead of cancelling', () => {
  const calls = []; const native = {start() {}, stop() {calls.push('stop');},
    startSession(lang, id) {calls.push({lang, id});}, finish() {calls.push('finish');}};
  const e = environment(native); e.win.KotobaVoiceSearch.start(null, {global: true});
  const active = calls.find(x => x.id);
  e.win.KotobaVoiceSearch._nativePartial('Where are', active.id);
  e.get('voice-search-stop').fire('click');
  assert.equal(calls[calls.length - 1], 'finish');
  e.win.KotobaVoiceSearch._nativeResults(JSON.stringify(['Where are you from?', 'Where are you from']), active.id);
  assert.equal(e.get('voice-search-transcript').value, 'Where are you from?');
  assert.equal(e.win.location.href, '/original');
  e.get('voice-search-use').fire('click');
  assert.equal(e.win.location.href, '/search?q=Where%20are%20you%20from%3F');
});

test('Native stale callbacks cannot replace a newer session', () => {
  const requests = [], native = {start() {}, stop() {}, startSession(lang, id) {requests.push(id);}};
  const e = environment(native); e.win.KotobaVoiceSearch.start(null, {global: true});
  e.win.KotobaVoiceSearch.start(null, {global: true});
  e.win.KotobaVoiceSearch._nativeResults('["old"]', requests[0]);
  assert.equal(e.get('voice-search-transcript').value, '');
  e.win.KotobaVoiceSearch._nativeResults('["水をください。"]', requests[1]);
  assert.equal(e.get('voice-search-transcript').value, '水をください。');
});

test('Selecting an alternative uses that phrase, not the first suggestion', () => {
  const native = {start() {}, stop() {}, startSession(lang, id) {this.id = id;}};
  const e = environment(native); e.win.KotobaVoiceSearch.start(null, {global: true});
  e.win.KotobaVoiceSearch._nativeResults('["understand","stand"]', native.id);
  e.get('voice-search-alternatives').children[0].fire('click');
  e.get('voice-search-use').fire('click');
  assert.equal(e.win.location.href, '/search?q=stand');
});

test('Local voice input emits filter events only after user confirmation', () => {
  const e = environment(); const input = new e.Element(); let changes = 0;
  input.addEventListener('input', () => changes++);
  e.win.KotobaVoiceSearch.start(input, {});
  e.recordings[0].onresult(result('water')); e.recordings[0].onend();
  assert.equal(input.value, '');
  e.get('voice-search-use').fire('click');
  assert.equal(input.value, 'water'); assert.equal(changes, 1);
  assert.equal(e.win.location.href, '/original');
});

test('Typed and spoken local filters keep English word boundaries and kana normalization', () => {
  const ctx = {window: {}};
  vm.runInNewContext(fs.readFileSync(__dirname + '/static/js/search-match.js', 'utf8'), ctx);
  const match = ctx.window.KotobaSearchMatch.matches;
  assert.equal(match('understand, comprehension', 'Stand.'), false);
  assert.equal(match('standard', 'stand'), false);
  assert.equal(match('立つ たつ tatsu to stand, stand up', 'Stand.'), true);
  assert.equal(match('ご飯 ごはん gohan rice', 'ｺﾞﾊﾝ'), true);
  assert.equal(match('東京 とうきょう tōkyō', 'tokyo'), true);
  assert.equal(match('か', 'が'), false);
});

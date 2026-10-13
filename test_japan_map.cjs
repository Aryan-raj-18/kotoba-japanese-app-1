// DOM integration checks. Native rendering and device gestures still need device QA.
// Requires jsdom@26.1.0 and the project's Python/Flask environment.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { JSDOM } = require(process.env.JSDOM_MODULE || 'jsdom');
const rendered = spawnSync(process.env.KOTOBA_TEST_PYTHON || 'python', ['-c', 'from app import app; print(app.test_client().get("/japan").data.decode())'], { cwd: __dirname, encoding: 'utf8' });
assert.equal(rendered.status, 0, rendered.stderr);
let checks = 0;
function check(name, callback) { callback(); checks++; console.log(`PASS ${name}`); }

function setup(width = 760) {
  const dom = new JSDOM(rendered.stdout, { url: 'http://localhost/japan', runScripts: 'outside-only', pretendToBeVisual: true });
  const w = dom.window, d = w.document, map = d.getElementById('japan-map');
  const errors = [];
  w.addEventListener('error', event => errors.push(event.error?.message || event.message));
  w.Element.prototype.scrollIntoView = function () {};
  w.DOMPoint = class {
    constructor(x, y) { this.x = x; this.y = y; }
    matrixTransform(m) { return new w.DOMPoint(this.x * m.a + this.y * (m.c || 0) + m.e, this.x * (m.b || 0) + this.y * m.d + m.f); }
  };
  map.createSVGPoint = () => new w.DOMPoint(0, 0);
  map.getScreenCTM = () => {
    const [x, y, vw] = map.getAttribute('viewBox').split(/\s+/).map(Number), scale = width / vw;
    return { a: scale, d: scale, e: -x * scale, f: -y * scale,
      inverse: () => ({ a: 1 / scale, d: 1 / scale, e: x, f: y }) };
  };
  const captures = new Set();
  map.hasPointerCapture = id => captures.has(id);
  map.setPointerCapture = id => captures.add(id);
  w.ResizeObserver = class { observe() {} };
  w.fetch = async () => ({ ok: true, json: async () => ({ visited_ids: [], visited_count: 0, first_time: false }) });
  const config = [...d.querySelectorAll('script:not([src])')].find(el => el.textContent.includes('window.JAPAN_EXPLORER_DATA'));
  w.eval(config.textContent);
  for (const name of ['search-match', 'japan_geography', 'japan_map', 'japan_explorer']) w.eval(fs.readFileSync(path.join(__dirname, `static/js/${name}.js`), 'utf8'));
  const pointer = (type, id, x, y, touch = false, target = map) => {
    const event = new w.MouseEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0 });
    Object.defineProperties(event, { pointerId: { value: id }, pointerType: { value: touch ? 'touch' : 'mouse' } });
    target.dispatchEvent(event);
  };
  return { dom, w, d, map, pointer, errors, zoom: () => Number(map.dataset.zoom), view: () => map.getAttribute('viewBox'), button: id => d.getElementById(id).click() };
}

(async () => {
  const t = setup();
  check('47 geographic prefectures and 47 matching capital pins', () => {
    assert.equal(t.d.querySelectorAll('.jp-prefecture').length, 47);
    assert.equal(t.d.querySelectorAll('.jp-map-pin').length, 47);
    for (const p of t.w.JAPAN_EXPLORER_DATA.places) {
      assert.ok(t.d.querySelector(`[data-prefecture="${p.id}"]`));
      assert.ok(t.d.querySelector(`[data-place="${p.id}"]`));
    }
  });
  check('zoom starts at all Japan and cannot go below 100%', () => { assert.equal(t.zoom(), 1); assert.equal(t.d.getElementById('japan-zoom-out').disabled, true); });
  check('button zoom stops at 800%', () => {
    for (let i = 0; i < 12 && !t.d.getElementById('japan-zoom-in').disabled; i++) t.button('japan-zoom-in');
    assert.equal(t.zoom(), 8); assert.equal(t.d.getElementById('japan-zoom-in').disabled, true);
  });
  check('reset restores the whole geographic extent', () => { t.button('japan-map-reset'); assert.equal(t.view(), '0 0 760 920'); });
  check('mouse wheel zooms around the cursor', () => {
    const before = t.map.getScreenCTM().inverse();
    const anchor = new t.w.DOMPoint(410, 420).matrixTransform(before);
    const event = new t.w.WheelEvent('wheel', { deltaY: -100, clientX: 410, clientY: 420, cancelable: true });
    t.map.dispatchEvent(event); const after = anchor.matrixTransform(t.map.getScreenCTM());
    assert.ok(t.zoom() > 1); assert.ok(event.defaultPrevented);
    assert.ok(Math.abs(after.x - 410) < .01 && Math.abs(after.y - 420) < .01);
  });
  check('arrow keys pan and Home resets', () => {
    const before = t.view(); t.map.dispatchEvent(new t.w.KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
    assert.notEqual(t.view(), before); t.map.dispatchEvent(new t.w.KeyboardEvent('keydown', { key: 'Home', bubbles: true })); assert.equal(t.zoom(), 1);
  });
  check('region filtering focuses the map and disables other prefectures', () => {
    t.d.querySelector('[data-region="Kanto"]').click(); assert.ok(t.zoom() > 1);
    assert.equal(t.d.querySelector('[data-prefecture="hokkaido"]').getAttribute('tabindex'), '-1');
    assert.equal(t.d.querySelectorAll('.japan-place-card').length, 7);
    t.d.querySelector('[data-region="All"]').click(); assert.equal(t.zoom(), 1);
  });
  check('city search focuses the matching capital', () => {
    const search = t.d.getElementById('japan-search'); search.value = 'Sapporo'; search.dispatchEvent(new t.w.Event('input'));
    assert.equal(t.d.querySelectorAll('.japan-place-card').length, 1); assert.ok(t.zoom() > 1); assert.ok(t.d.getElementById('japan-list-title').textContent.includes('Sapporo'));
    search.value = ''; search.dispatchEvent(new t.w.Event('input'));
  });
  check('all 47 prefectures open their own capital details', () => {
    for (const p of t.w.JAPAN_EXPLORER_DATA.places) {
      t.d.querySelector(`[data-prefecture="${p.id}"]`).dispatchEvent(new t.w.KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      assert.ok(t.d.querySelector('#japan-drawer h2').textContent.startsWith(p.city_en));
      assert.equal(t.d.getElementById('japan-drawer').getAttribute('aria-hidden'), 'false');
      t.button('japan-drawer-close');
    }
  });
  check('city labels increase when zooming into a region', () => {
    t.button('japan-map-reset');
    const count = () => [...t.d.querySelectorAll('.jp-capital-label')].filter(el => el.style.visibility === 'visible').length;
    const full = count(); t.d.querySelector('[data-region="Kanto"]').click();
    assert.ok(count() >= 4); assert.ok(t.zoom() > 1); assert.ok(full >= 6);
  });
  check('dragging a capital pans without opening its details', () => {
    const pin = t.d.querySelector('[data-place="tokyo"]'), dot = pin.querySelector('.jp-pin-dot');
    const screen = new t.w.DOMPoint(Number(dot.getAttribute('cx')), Number(dot.getAttribute('cy'))).matrixTransform(t.map.getScreenCTM());
    const before = t.view(); t.pointer('pointerdown', 1, screen.x, screen.y, false, dot); t.pointer('pointermove', 1, screen.x + 45, screen.y + 25); t.pointer('pointerup', 1, screen.x + 45, screen.y + 25);
    pin.dispatchEvent(new t.w.MouseEvent('click', { bubbles: true, cancelable: true, clientX: screen.x + 45, clientY: screen.y + 25 }));
    assert.notEqual(t.view(), before); assert.equal(t.d.getElementById('japan-drawer').getAttribute('aria-hidden'), 'true');
  });
  await new Promise(resolve => setTimeout(resolve, 370));
  check('overlapping pin hit areas choose the nearest capital', () => {
    const tokyo = t.d.querySelector('[data-place="tokyo"] .jp-pin-dot'), other = t.d.querySelector('[data-place="kanagawa"]');
    const q = new t.w.DOMPoint(Number(tokyo.getAttribute('cx')), Number(tokyo.getAttribute('cy'))).matrixTransform(t.map.getScreenCTM());
    other.dispatchEvent(new t.w.MouseEvent('click', { bubbles: true, clientX: q.x, clientY: q.y }));
    assert.ok(t.d.querySelector('#japan-drawer h2').textContent.startsWith('Tokyo')); t.button('japan-drawer-close');
  });
  check('expanded map has a close control and Escape restores the page', () => {
    t.button('japan-map-expand'); assert.ok(t.d.body.classList.contains('japan-map-expanded')); assert.equal(t.d.getElementById('japan-map-wrap').getAttribute('aria-modal'), 'true');
    t.d.dispatchEvent(new t.w.KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); assert.ok(!t.d.body.classList.contains('japan-map-expanded'));
  });
  check('the scale bar updates as the map zooms', () => {
    t.d.querySelector('[data-region="All"]').click(); t.button('japan-map-reset');
    const before = t.d.getElementById('japan-map-scale-label').textContent;
    for (let i = 0; i < 4; i++) t.button('japan-zoom-in');
    assert.notEqual(t.d.getElementById('japan-map-scale-label').textContent, before);
  });
  const mobile = setup(348);
  check('two-finger pinch zooms on a mobile viewport', () => {
    mobile.pointer('pointerdown', 11, 135, 205, true); mobile.pointer('pointerdown', 12, 205, 205, true);
    mobile.pointer('pointermove', 11, 95, 205, true); mobile.pointer('pointermove', 12, 245, 205, true);
    mobile.pointer('pointerup', 11, 95, 205, true); mobile.pointer('pointerup', 12, 245, 205, true);
    assert.ok(mobile.zoom() > 1.8); assert.equal(mobile.d.getElementById('japan-drawer').getAttribute('aria-hidden'), 'true');
  });
  check('lifting one pinch finger preserves queued zoom before the remaining pan', () => {
    mobile.button('japan-map-reset');
    mobile.pointer('pointerdown',51,135,205,true);mobile.pointer('pointerdown',52,205,205,true);
    mobile.pointer('pointermove',51,95,205,true);mobile.pointer('pointermove',52,245,205,true);
    mobile.pointer('pointerup',51,95,205,true);
    mobile.pointer('pointermove',52,265,220,true);mobile.pointer('pointerup',52,265,220,true);
    assert.ok(mobile.zoom()>1.8);
  });
  check('single-finger drag pans after a pinch', () => {
    const before = mobile.view(); mobile.pointer('pointerdown', 20, 175, 205, true); mobile.pointer('pointermove', 20, 200, 220, true); mobile.pointer('pointerup', 20, 200, 220, true); assert.notEqual(mobile.view(), before);
  });
  check('touch cancellation leaves subsequent zoom controls working', () => {
    mobile.pointer('pointerdown', 30, 140, 200, true); mobile.pointer('pointercancel', 30, 140, 200, true); mobile.button('japan-map-reset'); assert.equal(mobile.zoom(), 1);
  });
  check('transferring touch capture from a prefecture keeps the drag active', () => {
    mobile.button('japan-zoom-in'); const area = mobile.d.querySelector('[data-prefecture="tokyo"]');
    mobile.pointer('pointerdown', 40, 170, 200, true, area); mobile.pointer('pointermove', 40, 190, 215, true);
    const before = mobile.view(); mobile.pointer('lostpointercapture', 40, 190, 215, true, area);
    mobile.pointer('pointermove', 40, 210, 225, true); mobile.pointer('pointerup',40,210,225,true); assert.notEqual(mobile.view(), before);
    mobile.pointer('pointerup', 40, 210, 225, true);
  });
  check('map interactions finish without JavaScript exceptions', () => { assert.deepEqual(t.errors, []); assert.deepEqual(mobile.errors, []); });
  if (process.env.KOTOBA_MAP_SVG) {
    const preview = setup(), el = preview.map;
    el.setAttribute('xmlns', 'http://www.w3.org/2000/svg'); el.setAttribute('width', '760'); el.setAttribute('height', '920');
    const style = preview.d.createElementNS('http://www.w3.org/2000/svg', 'style');
    style.textContent = fs.readFileSync(path.join(__dirname, 'static/css/japan-map.css'), 'utf8').replace(/var\(--serif-body\)/g, 'serif') + '.jp-pin-dot{fill:#fff;stroke:#b7472a}.jp-pin-hit{fill:transparent}.jp-pin-pulse{opacity:0}.jp-map-pin.filtered-out{display:none}.japan-plane,.japan-route-train{display:none}';
    el.insertBefore(style, el.firstChild); fs.writeFileSync(process.env.KOTOBA_MAP_SVG, el.outerHTML); preview.dom.window.close();
  }
  console.log(`All ${checks} Japan map interaction checks passed (DOM simulation).`);
  mobile.dom.window.close(); t.dom.window.close();
})().catch(error => { console.error(error); process.exitCode = 1; });

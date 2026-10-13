// Offline SVG camera: mouse, touch, keyboard, and accessible map controls.
(() => {
  'use strict';
  window.KotobaJapanMap = function (map, options = {}) {
    const base = { x: 0, y: 0, width: 760, height: 920 };
    const maxZoom = 8;
    let view = { ...base }, gesture = null, moved = false, suppressClickUntil = 0;
    let pendingFrame = 0, pendingCommit = null;
    const pointers = new Map();
    const wrap = map.closest('.japan-map-wrap');
    const readout = document.getElementById('japan-map-zoom-value');
    const plus = document.getElementById('japan-zoom-in');
    const minus = document.getElementById('japan-zoom-out');
    const expand = document.getElementById('japan-map-expand');
    const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
    const zoom = () => base.width / view.width;

    function applyCommit(next) {
      const width = clamp(next.width, base.width / maxZoom, base.width);
      const height = width * base.height / base.width;
      view = { x: clamp(next.x, 0, base.width - width), y: clamp(next.y, 0, base.height - height), width, height };
      map.setAttribute('viewBox', `${view.x} ${view.y} ${view.width} ${view.height}`);
      map.dataset.zoom = zoom().toFixed(3);
      if (readout) readout.textContent = `${Math.round(zoom() * 100)}%`;
      if (plus) plus.disabled = zoom() >= maxZoom - .001;
      if (minus) minus.disabled = zoom() <= 1.001;
      options.onChange?.({ ...view, zoom: zoom() });
    }

    // Pointer events may arrive much faster than the display can draw.
    // Coalesce drag/pinch updates to one SVG viewBox change per animation
    // frame, which prevents main-thread overwork and keeps map interaction
    // close to a stable 60 FPS (or the phone's higher refresh cadence).
    function scheduleCommit(next) {
      pendingCommit = next;
      if (pendingFrame) return;
      pendingFrame = requestAnimationFrame(() => {
        pendingFrame = 0;
        const target = pendingCommit;
        pendingCommit = null;
        if (target) applyCommit(target);
      });
    }

    function flushPending() {
      if (!pendingCommit) return;
      const target = pendingCommit;
      cancelAnimationFrame(pendingFrame);
      pendingFrame = 0; pendingCommit = null;
      applyCommit(target);
    }
    function commit(next) {
      if (pendingFrame) {
        cancelAnimationFrame(pendingFrame);
        pendingFrame = 0;
        pendingCommit = null;
      }
      applyCommit(next);
    }

    function worldPoint(x, y) {
      const matrix = map.getScreenCTM();
      if (!matrix) return { x: view.x + view.width / 2, y: view.y + view.height / 2 };
      const point = map.createSVGPoint(); point.x = x; point.y = y;
      return point.matrixTransform(matrix.inverse());
    }

    function zoomBy(factor, anchor = { x: view.x + view.width / 2, y: view.y + view.height / 2 }) {
      const width = clamp(view.width / factor, base.width / maxZoom, base.width);
      const ratio = width / view.width;
      commit({ x: anchor.x - (anchor.x - view.x) * ratio, y: anchor.y - (anchor.y - view.y) * ratio, width });
    }

    function fit(bounds, padding = 55, limit = maxZoom) {
      const [left, top, right, bottom] = bounds;
      const width = clamp(Math.max(right - left + padding * 2, (bottom - top + padding * 2) * base.width / base.height), base.width / limit, base.width);
      commit({ x: (left + right - width) / 2, y: (top + bottom - width * base.height / base.width) / 2, width });
    }

    function beginGesture() {
      const points = [...pointers.values()];
      if (points.length === 1) {
        gesture = { type: 'pan', point: points[0], view: { ...view }, scale: map.getScreenCTM()?.a || 1 };
      } else if (points.length >= 2) {
        const [a, b] = points;
        gesture = { type: 'pinch', view: { ...view }, distance: Math.max(1, Math.hypot(a.x - b.x, a.y - b.y)),
          anchor: worldPoint((a.x + b.x) / 2, (a.y + b.y) / 2) };
        moved = true;
      } else gesture = null;
    }

    map.addEventListener('pointerdown', event => {
      flushPending();
      if (event.pointerType === 'mouse' && event.button !== 0) return;
      if (!pointers.size) moved = false;
      pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
      beginGesture();
    });
    map.addEventListener('pointermove', event => {
      if (!pointers.has(event.pointerId) || !gesture) return;
      pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (gesture.type === 'pan') {
        const dx = event.clientX - gesture.point.x, dy = event.clientY - gesture.point.y;
        if (!moved && Math.hypot(dx, dy) < 5) return;
        moved = true;
        scheduleCommit({ x: gesture.view.x - dx / gesture.scale, y: gesture.view.y - dy / gesture.scale, width: gesture.view.width });
      } else {
        const [a, b] = [...pointers.values()];
        const distance = Math.max(1, Math.hypot(a.x - b.x, a.y - b.y));
        const center = worldPoint((a.x + b.x) / 2, (a.y + b.y) / 2);
        const fx = (center.x - view.x) / view.width, fy = (center.y - view.y) / view.height;
        const width = clamp(gesture.view.width * gesture.distance / distance, base.width / maxZoom, base.width);
        scheduleCommit({ x: gesture.anchor.x - fx * width, y: gesture.anchor.y - fy * width * base.height / base.width, width });
      }
      wrap?.classList.add('is-dragging');
      if (!map.hasPointerCapture(event.pointerId)) map.setPointerCapture(event.pointerId);
    });
    function endPointer(event) {
      flushPending();
      if (!pointers.has(event.pointerId)) return;
      if (moved) suppressClickUntil = performance.now() + 350;
      pointers.delete(event.pointerId);
      beginGesture();
      if (!pointers.size) wrap?.classList.remove('is-dragging');
    }
    map.addEventListener('pointerup', endPointer);
    map.addEventListener('pointercancel', endPointer);
    // Touch starts with implicit capture on the tapped path. Transferring
    // capture to the SVG emits a bubbled event from that path, not a lost drag.
    map.addEventListener('lostpointercapture', event => { if (event.target === map) endPointer(event); });
    window.addEventListener('pointerup', endPointer);
    window.addEventListener('pointercancel', endPointer);
    map.addEventListener('click', event => {
      if (performance.now() < suppressClickUntil) { event.preventDefault(); event.stopImmediatePropagation(); }
    }, true);
    map.addEventListener('wheel', event => {
      event.preventDefault();
      const delta = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? 400 : 1);
      zoomBy(Math.exp(-clamp(delta, -140, 140) * .004), worldPoint(event.clientX, event.clientY));
    }, { passive: false });
    map.addEventListener('dblclick', event => {
      if (event.target.closest('.jp-map-pin, .jp-prefecture')) return;
      event.preventDefault(); zoomBy(1.7, worldPoint(event.clientX, event.clientY));
    });
    map.addEventListener('keydown', event => {
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      const step = event.shiftKey ? .3 : .12;
      const actions = {
        '+': () => zoomBy(1.4), '=': () => zoomBy(1.4), '-': () => zoomBy(1 / 1.4),
        'Home': () => commit(base), '0': () => commit(base),
        'ArrowLeft': () => commit({ ...view, x: view.x - view.width * step }),
        'ArrowRight': () => commit({ ...view, x: view.x + view.width * step }),
        'ArrowUp': () => commit({ ...view, y: view.y - view.height * step }),
        'ArrowDown': () => commit({ ...view, y: view.y + view.height * step })
      };
      if (actions[event.key]) { event.preventDefault(); actions[event.key](); }
    });
    plus?.addEventListener('click', () => zoomBy(1.4));
    minus?.addEventListener('click', () => zoomBy(1 / 1.4));
    document.getElementById('japan-map-reset')?.addEventListener('click', () => commit(base));
    function setExpanded(expanded) {
      wrap?.classList.toggle('is-expanded', expanded);
      document.body.classList.toggle('japan-map-expanded', expanded);
      expand?.setAttribute('aria-pressed', String(expanded));
      expand?.setAttribute('aria-label', expanded ? 'Close expanded map' : 'Expand map');
      if (expand) expand.textContent = expanded ? '×' : '⛶';
      // Expanded view behaves as a modal; keep keyboard focus in the map.
      wrap?.setAttribute('role', expanded ? 'dialog' : 'group');
      wrap?.setAttribute('aria-modal', expanded ? 'true' : 'false');
      if (expanded) map.focus(); else expand?.focus();
    }
    expand?.addEventListener('click', () => setExpanded(!wrap?.classList.contains('is-expanded')));
    document.addEventListener('keydown', event => {
      if (!wrap?.classList.contains('is-expanded')) return;
      if (event.key === 'Escape') { event.preventDefault(); setExpanded(false); }
      if (event.key === 'Tab') {
        const focusable = [...wrap.querySelectorAll('button:not(:disabled), [tabindex="0"]')].filter(el => el.getAttribute('aria-hidden') !== 'true');
        const first = focusable[0], last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    });
    commit(base);
    return { zoomBy, fit, setExpanded, reset: () => commit(base), getView: () => ({ ...view, zoom: zoom() }) };
  };
})();

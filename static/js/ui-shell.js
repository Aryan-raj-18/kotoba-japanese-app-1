/*
 * Kotoba Immersive UI Shell
 * -------------------------
 * Presentation-only layer. It never replaces page links, form actions,
 * learning data, APIs, or page-specific JavaScript.
 *
 * Wallpaper support is also presentation-only: the selected image/GIF is
 * stored as a Blob in IndexedDB on this device and is never uploaded.
 * The saved framing is only a local zoom/position preference, so animated
 * GIFs stay animated instead of being flattened by a canvas crop.
 */
(function () {
  'use strict';

  var DB_NAME = 'kotoba-ui-shell';
  var DB_VERSION = 1;
  var STORE = 'preferences';
  var WALLPAPER_KEY = 'wallpaper';
  var DIM_KEY = 'kotoba:wallpaper:dim';
  var FRAME_KEY = 'kotoba:wallpaper:frame';
  var DEFAULT_DIM = 60;
  var MAX_WALLPAPER_BYTES = 60 * 1024 * 1024;
  var currentObjectUrl = null;
  var currentImageDims = null;
  var currentFrame = readFrame();
  var pendingCrop = null;

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function defaultFrame() {
    return { x: 0.5, y: 0.5, zoom: 1 };
  }

  function normalizeFrame(value) {
    value = value || {};
    var x = Number(value.x);
    var y = Number(value.y);
    var zoom = Number(value.zoom);
    if (!isFinite(x)) x = 0.5;
    if (!isFinite(y)) y = 0.5;
    if (!isFinite(zoom) || zoom <= 0) zoom = 1;
    return {
      x: clamp(x, 0, 1),
      y: clamp(y, 0, 1),
      zoom: clamp(zoom, 1, 3.5)
    };
  }

  function readFrame() {
    try {
      var raw = localStorage.getItem(FRAME_KEY);
      return raw ? normalizeFrame(JSON.parse(raw)) : defaultFrame();
    } catch (e) { return defaultFrame(); }
  }

  function saveFrame(frame) {
    currentFrame = normalizeFrame(frame);
    try { localStorage.setItem(FRAME_KEY, JSON.stringify(currentFrame)); } catch (e) { /* ignore */ }
  }

  function clearSavedFrame() {
    currentFrame = defaultFrame();
    try { localStorage.removeItem(FRAME_KEY); } catch (e) { /* ignore */ }
  }

  function readDim() {
    try {
      var v = localStorage.getItem(DIM_KEY);
      return v !== null ? Number(v) : DEFAULT_DIM;
    } catch (e) { return DEFAULT_DIM; }
  }

  function applyDim(pct) {
    document.documentElement.style.setProperty('--wallpaper-scrim', pct / 100);
  }

  function saveDim(pct) {
    try { localStorage.setItem(DIM_KEY, String(pct)); } catch (e) { /* ignore */ }
  }

  applyDim(readDim());

  function iconFor(label) {
    var map = { Home: '⌂', Learn: '学', Review: '↻', Explore: '探', Progress: '◔' };
    return map[label] || '•';
  }

  function makeBottomNav() {
    if (document.querySelector('.kotoba-bottom-nav')) return;

    var nav = document.createElement('nav');
    nav.className = 'kotoba-bottom-nav';
    nav.setAttribute('aria-label', 'Quick navigation');

    var current = window.location.pathname.replace(/\/$/, '') || '/';
    var items = [
      { label: 'Home', href: '/', match: ['/'] },
      { label: 'Learn', href: '/roadmap', match: ['/roadmap'] },
      { label: 'Review', href: '/review', match: ['/review','/mistakes','/favorites','/flashcards','/practice','/kanji/practice'] },
      { label: 'Explore', href: '/explore', match: ['/explore','/hiragana','/katakana','/kanji','/jlpt','/verbs','/everyday','/stories','/conversations','/write','/writing-practice'] },
      { label: 'Progress', href: '/dashboard', match: ['/dashboard','/streak'] }
    ];

    items.forEach(function (item) {
      var a = document.createElement('a');
      a.href = item.href;
      a.innerHTML = '<span class="nav-icon" data-theme-icon="' + item.label.toLowerCase() + '" aria-hidden="true">' + iconFor(item.label) + '</span>' +
                    '<span>' + item.label + '</span>';
      var active = item.match.some(function (path) {
        if (path === '/') return current === '/';
        return current === path || current.indexOf(path + '/') === 0;
      });
      if (active) a.classList.add('active');
      nav.appendChild(a);
    });

    document.body.appendChild(nav);
    if(window.KotobaThemeIcons)window.KotobaThemeIcons.refresh();
  }

  function openDb() {
    return new Promise(function (resolve, reject) {
      if (!window.indexedDB) {
        reject(new Error('IndexedDB is unavailable'));
        return;
      }
      var request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = function () {
        var db = request.result;
        if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE);
      };
      request.onsuccess = function () { resolve(request.result); };
      request.onerror = function () { reject(request.error || new Error('Database error')); };
    });
  }

  function dbGet(key) {
    return openDb().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(STORE, 'readonly');
        var req = tx.objectStore(STORE).get(key);
        req.onsuccess = function () { resolve(req.result || null); };
        req.onerror = function () { reject(req.error || new Error('Read error')); };
        tx.oncomplete = function () { db.close(); };
      });
    });
  }

  function dbPut(key, value) {
    return openDb().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(STORE, 'readwrite');
        tx.objectStore(STORE).put(value, key);
        tx.oncomplete = function () { db.close(); resolve(); };
        tx.onerror = function () { reject(tx.error || new Error('Write error')); };
      });
    });
  }

  function dbDelete(key) {
    return openDb().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(STORE, 'readwrite');
        tx.objectStore(STORE).delete(key);
        tx.oncomplete = function () { db.close(); resolve(); };
        tx.onerror = function () { reject(tx.error || new Error('Delete error')); };
      });
    });
  }

  function loadImageDimensions(url) {
    return new Promise(function (resolve, reject) {
      var image = new Image();
      image.onload = function () {
        var width = image.naturalWidth || image.width;
        var height = image.naturalHeight || image.height;
        if (!width || !height) reject(new Error('Image has no readable dimensions'));
        else resolve({ width: width, height: height });
      };
      image.onerror = function () { reject(new Error('Image could not be decoded')); };
      image.src = url;
    });
  }

  function layoutFor(dims, viewWidth, viewHeight, frame) {
    frame = normalizeFrame(frame);
    var scale = Math.max(viewWidth / dims.width, viewHeight / dims.height) * frame.zoom;
    var renderWidth = Math.max(1, dims.width * scale);
    var renderHeight = Math.max(1, dims.height * scale);
    var excessX = Math.max(0, renderWidth - viewWidth);
    var excessY = Math.max(0, renderHeight - viewHeight);
    return {
      width: renderWidth,
      height: renderHeight,
      excessX: excessX,
      excessY: excessY,
      left: -excessX * frame.x,
      top: -excessY * frame.y
    };
  }

  function paintFramedBackground(element, url, dims, frame, width, height) {
    if (!element || !url) return null;
    element.style.backgroundImage = 'url("' + url.replace(/"/g, '%22') + '")';
    if (!dims || !width || !height) {
      element.style.backgroundSize = 'cover';
      element.style.backgroundPosition = 'center';
      return null;
    }
    var layout = layoutFor(dims, width, height, frame);
    element.style.backgroundSize = layout.width + 'px ' + layout.height + 'px';
    element.style.backgroundPosition = layout.left + 'px ' + layout.top + 'px';
    return layout;
  }

  function applyCurrentWallpaperLayout() {
    var wallpaper = document.querySelector('.kotoba-wallpaper');
    if (!wallpaper || !currentObjectUrl) return;
    paintFramedBackground(
      wallpaper,
      currentObjectUrl,
      currentImageDims,
      currentFrame,
      window.innerWidth || document.documentElement.clientWidth,
      window.innerHeight || document.documentElement.clientHeight
    );
  }

  function setWallpaper(blob, frame) {
    if (currentObjectUrl) URL.revokeObjectURL(currentObjectUrl);
    currentObjectUrl = URL.createObjectURL(blob);
    currentImageDims = null;
    currentFrame = normalizeFrame(frame || readFrame());

    var wallpaper = document.querySelector('.kotoba-wallpaper');
    if (!wallpaper) {
      wallpaper = document.createElement('div');
      wallpaper.className = 'kotoba-wallpaper';
      wallpaper.setAttribute('aria-hidden', 'true');
      document.body.prepend(wallpaper);
    }
    paintFramedBackground(wallpaper, currentObjectUrl, null, currentFrame, 0, 0);
    document.body.classList.add('has-kotoba-wallpaper');

    var clear = document.getElementById('wallpaper-clear');
    if (clear) clear.hidden = false;
    var reposition = document.getElementById('wallpaper-reposition');
    if (reposition) reposition.hidden = false;
    var dimRow = document.getElementById('wallpaper-dim-row');
    if (dimRow) dimRow.hidden = false;

    loadImageDimensions(currentObjectUrl).then(function (dims) {
      currentImageDims = dims;
      applyCurrentWallpaperLayout();
    }).catch(function () {
      // CSS cover remains a safe fallback for an unusual but valid image.
    });
  }

  function clearWallpaper() {
    if (currentObjectUrl) {
      URL.revokeObjectURL(currentObjectUrl);
      currentObjectUrl = null;
    }
    currentImageDims = null;
    var wallpaper = document.querySelector('.kotoba-wallpaper');
    if (wallpaper) wallpaper.remove();
    document.body.classList.remove('has-kotoba-wallpaper');
    dbDelete(WALLPAPER_KEY).catch(function () {});
    clearSavedFrame();
    var clear = document.getElementById('wallpaper-clear');
    if (clear) clear.hidden = true;
    var reposition = document.getElementById('wallpaper-reposition');
    if (reposition) reposition.hidden = true;
    var dimRow = document.getElementById('wallpaper-dim-row');
    if (dimRow) dimRow.hidden = true;
  }

  function loadWallpaper() {
    dbGet(WALLPAPER_KEY).then(function (blob) {
      if (blob instanceof Blob && blob.size > 0) setWallpaper(blob, readFrame());
    }).catch(function () {});
  }

  function ensureCropEditor() {
    var existing = document.getElementById('wallpaper-crop-overlay');
    if (existing) return existing;

    var overlay = document.createElement('div');
    overlay.className = 'wallpaper-crop-overlay';
    overlay.id = 'wallpaper-crop-overlay';
    overlay.hidden = true;
    overlay.innerHTML =
      '<section class="wallpaper-crop-dialog" role="dialog" aria-modal="true" aria-labelledby="wallpaper-crop-title">' +
        '<div class="wallpaper-crop-head">' +
          '<div><p class="wallpaper-crop-kicker">背景 · Wallpaper</p><h3 id="wallpaper-crop-title">Choose the visible area</h3></div>' +
          '<button type="button" class="wallpaper-crop-close" id="wallpaper-crop-close" aria-label="Close crop editor">×</button>' +
        '</div>' +
        '<p class="wallpaper-crop-help">Drag the image to move it. Use Zoom to choose how much of the photo or GIF appears on screen.</p>' +
        '<div class="wallpaper-crop-stage-wrap">' +
          '<div class="wallpaper-crop-frame" id="wallpaper-crop-frame" aria-label="Wallpaper crop preview">' +
            '<div class="wallpaper-crop-image" id="wallpaper-crop-image"></div>' +
          '</div>' +
        '</div>' +
        '<div class="wallpaper-crop-controls">' +
          '<label for="wallpaper-crop-zoom"><span>Zoom</span><strong id="wallpaper-crop-zoom-value">100%</strong></label>' +
          '<input type="range" id="wallpaper-crop-zoom" min="100" max="350" step="1" value="100">' +
          '<button type="button" class="wallpaper-crop-reset" id="wallpaper-crop-reset">Center image</button>' +
        '</div>' +
        '<div class="wallpaper-crop-actions">' +
          '<button type="button" class="wallpaper-crop-cancel" id="wallpaper-crop-cancel">Cancel</button>' +
          '<button type="button" class="wallpaper-crop-apply" id="wallpaper-crop-apply">Use this area</button>' +
        '</div>' +
      '</section>';
    document.body.appendChild(overlay);

    var frame = overlay.querySelector('#wallpaper-crop-frame');
    var zoom = overlay.querySelector('#wallpaper-crop-zoom');
    var zoomValue = overlay.querySelector('#wallpaper-crop-zoom-value');
    var dragging = false;
    var lastX = 0;
    var lastY = 0;

    function sizeCropFrame() {
      if (!pendingCrop) return;
      var viewportWidth = window.innerWidth || 360;
      var viewportHeight = window.innerHeight || 720;
      var ratio = viewportWidth / Math.max(1, viewportHeight);
      var maxWidth = Math.min(viewportWidth - 54, 560);
      var maxHeight = Math.min(viewportHeight * 0.52, 520);
      var width = maxWidth;
      var height = width / ratio;
      if (height > maxHeight) {
        height = maxHeight;
        width = height * ratio;
      }
      frame.style.width = Math.max(150, Math.round(width)) + 'px';
      frame.style.height = Math.max(210, Math.round(height)) + 'px';
    }

    function renderCrop() {
      if (!pendingCrop || !pendingCrop.dims) return null;
      sizeCropFrame();
      zoom.value = String(Math.round(pendingCrop.frame.zoom * 100));
      zoomValue.textContent = Math.round(pendingCrop.frame.zoom * 100) + '%';
      return paintFramedBackground(
        overlay.querySelector('#wallpaper-crop-image'),
        pendingCrop.url,
        pendingCrop.dims,
        pendingCrop.frame,
        frame.clientWidth,
        frame.clientHeight
      );
    }

    function closeCropEditor() {
      overlay.hidden = true;
      document.body.classList.remove('wallpaper-crop-open');
      if (pendingCrop && pendingCrop.url) URL.revokeObjectURL(pendingCrop.url);
      pendingCrop = null;
    }

    frame.addEventListener('pointerdown', function (event) {
      if (!pendingCrop || !pendingCrop.dims) return;
      dragging = true;
      lastX = event.clientX;
      lastY = event.clientY;
      frame.classList.add('dragging');
      if (frame.setPointerCapture) frame.setPointerCapture(event.pointerId);
      event.preventDefault();
    });

    frame.addEventListener('pointermove', function (event) {
      if (!dragging || !pendingCrop || !pendingCrop.dims) return;
      var dx = event.clientX - lastX;
      var dy = event.clientY - lastY;
      lastX = event.clientX;
      lastY = event.clientY;
      var layout = layoutFor(pendingCrop.dims, frame.clientWidth, frame.clientHeight, pendingCrop.frame);
      if (layout.excessX > 0.5) pendingCrop.frame.x = clamp(pendingCrop.frame.x - dx / layout.excessX, 0, 1);
      if (layout.excessY > 0.5) pendingCrop.frame.y = clamp(pendingCrop.frame.y - dy / layout.excessY, 0, 1);
      renderCrop();
      event.preventDefault();
    });

    function endDrag(event) {
      if (!dragging) return;
      dragging = false;
      frame.classList.remove('dragging');
      if (event && frame.releasePointerCapture) {
        try { frame.releasePointerCapture(event.pointerId); } catch (e) { /* already released */ }
      }
    }
    frame.addEventListener('pointerup', endDrag);
    frame.addEventListener('pointercancel', endDrag);

    zoom.addEventListener('input', function () {
      if (!pendingCrop) return;
      pendingCrop.frame.zoom = Number(zoom.value) / 100;
      renderCrop();
    });

    frame.addEventListener('wheel', function (event) {
      if (!pendingCrop) return;
      var next = clamp(pendingCrop.frame.zoom + (event.deltaY < 0 ? 0.08 : -0.08), 1, 3.5);
      pendingCrop.frame.zoom = next;
      renderCrop();
      event.preventDefault();
    }, { passive: false });

    overlay.querySelector('#wallpaper-crop-reset').addEventListener('click', function () {
      if (!pendingCrop) return;
      pendingCrop.frame = defaultFrame();
      renderCrop();
      if (window.Sfx) Sfx.tap();
    });

    overlay.querySelector('#wallpaper-crop-close').addEventListener('click', closeCropEditor);
    overlay.querySelector('#wallpaper-crop-cancel').addEventListener('click', closeCropEditor);
    overlay.addEventListener('click', function (event) {
      if (event.target === overlay) closeCropEditor();
    });

    overlay.querySelector('#wallpaper-crop-apply').addEventListener('click', function () {
      if (!pendingCrop) return;
      var blob = pendingCrop.blob;
      var frameChoice = normalizeFrame(pendingCrop.frame);
      var shouldStoreBlob = pendingCrop.storeBlob;
      saveFrame(frameChoice);
      var done = function () {
        setWallpaper(blob, frameChoice);
        closeCropEditor();
        var progress = document.getElementById('wallpaper-progress');
        if (progress) progress.hidden = true;
        if (window.Sfx) Sfx.tap();
      };
      if (shouldStoreBlob) {
        dbPut(WALLPAPER_KEY, blob).then(done).catch(done);
      } else {
        done();
      }
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && !overlay.hidden) closeCropEditor();
    });

    window.addEventListener('resize', function () {
      if (!overlay.hidden && pendingCrop) renderCrop();
    });

    overlay._renderCrop = renderCrop;
    return overlay;
  }

  function openCropEditor(blob, options) {
    options = options || {};
    var overlay = ensureCropEditor();
    var url = URL.createObjectURL(blob);
    pendingCrop = {
      blob: blob,
      url: url,
      dims: null,
      frame: normalizeFrame(options.frame || defaultFrame()),
      storeBlob: options.storeBlob !== false
    };
    document.body.classList.add('wallpaper-crop-open');
    overlay.hidden = false;

    loadImageDimensions(url).then(function (dims) {
      if (!pendingCrop || pendingCrop.url !== url) return;
      pendingCrop.dims = dims;
      if (overlay._renderCrop) overlay._renderCrop();
    }).catch(function () {
      var progress = document.getElementById('wallpaper-progress');
      if (progress) {
        progress.hidden = false;
        progress.textContent = 'This image could not be previewed. Try another image.';
      }
      overlay.hidden = true;
      document.body.classList.remove('wallpaper-crop-open');
      URL.revokeObjectURL(url);
      pendingCrop = null;
    });
  }

  function buildWallpaperControls(panel) {
    if (!panel || panel.querySelector('.wallpaper-settings')) return;

    var section = document.createElement('div');
    section.className = 'wallpaper-settings';
    section.innerHTML =
      '<h4>背景 · Wallpaper</h4>' +
      '<div class="wallpaper-actions">' +
        '<button type="button" class="wallpaper-upload-btn" id="wallpaper-upload">Choose image / GIF</button>' +
        '<button type="button" class="wallpaper-reposition-btn" id="wallpaper-reposition" hidden>Adjust crop</button>' +
        '<button type="button" class="wallpaper-clear-btn" id="wallpaper-clear" hidden>Reset</button>' +
      '</div>' +
      '<input type="file" id="wallpaper-file" accept="image/*,.gif" hidden>' +
      '<p class="wallpaper-progress" id="wallpaper-progress" hidden></p>' +
      '<div class="wallpaper-dim-row" id="wallpaper-dim-row" hidden>' +
        '<label for="wallpaper-dim">Dim</label>' +
        '<input type="range" id="wallpaper-dim" min="15" max="90" value="' + DEFAULT_DIM + '">' +
      '</div>' +
      '<p class="wallpaper-hint">Choose a photo or GIF, then drag and zoom to select exactly which area appears behind the app. Stored only on this device — never uploaded.</p>';

    panel.appendChild(section);

    var upload = section.querySelector('#wallpaper-upload');
    var input = section.querySelector('#wallpaper-file');
    var reposition = section.querySelector('#wallpaper-reposition');
    var clear = section.querySelector('#wallpaper-clear');
    var progress = section.querySelector('#wallpaper-progress');
    var dimSlider = section.querySelector('#wallpaper-dim');

    dimSlider.value = readDim();

    upload.addEventListener('click', function () { input.click(); });
    input.addEventListener('change', function () {
      var file = input.files && input.files[0];
      input.value = '';
      if (!file) return;
      if (!file.type || file.type.indexOf('image/') !== 0) {
        progress.hidden = false;
        progress.textContent = 'That file doesn\u2019t look like an image or GIF.';
        return;
      }
      if (file.size > MAX_WALLPAPER_BYTES) {
        progress.hidden = false;
        progress.textContent = 'That file is larger than 60MB — try a smaller image or GIF.';
        return;
      }
      progress.hidden = true;
      openCropEditor(file, { frame: defaultFrame(), storeBlob: true });
    });

    reposition.addEventListener('click', function () {
      progress.hidden = true;
      dbGet(WALLPAPER_KEY).then(function (blob) {
        if (blob instanceof Blob && blob.size > 0) {
          openCropEditor(blob, { frame: readFrame(), storeBlob: false });
        }
      }).catch(function () {
        progress.hidden = false;
        progress.textContent = 'The saved wallpaper could not be opened. Choose it again.';
      });
    });

    clear.addEventListener('click', function () {
      clearWallpaper();
      progress.hidden = true;
      if (window.Sfx) Sfx.tap();
    });

    dimSlider.addEventListener('input', function () {
      var pct = Number(dimSlider.value);
      applyDim(pct);
      saveDim(pct);
    });
  }

  function init() {
    makeBottomNav();
    document.body.classList.add('kotoba-shell-ready');

    var panel = document.getElementById('settings-panel');
    buildWallpaperControls(panel);
    loadWallpaper();

    window.addEventListener('resize', applyCurrentWallpaperLayout);
    window.addEventListener('orientationchange', function () {
      setTimeout(applyCurrentWallpaperLayout, 100);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();

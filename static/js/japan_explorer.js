(() => {
  const payload = window.JAPAN_EXPLORER_DATA || {};
  const places = Array.isArray(payload.places) ? payload.places : [];
  if (!places.length) return;

  const NS = 'http://www.w3.org/2000/svg';
  const byId = new Map(places.map(p => [p.id, p]));
  const map = document.getElementById('japan-map');
  const islands = document.getElementById('japan-islands');
  const seasonLayer = document.getElementById('japan-season-layer');
  const routeLayer = document.getElementById('japan-route-layer');
  const pinLayer = document.getElementById('japan-pin-layer');
  const labelLayer = document.getElementById('japan-label-layer');
  const plane = document.getElementById('japan-plane');
  const train = document.getElementById('japan-train');
  const list = document.getElementById('japan-place-list');
  const countEl = document.getElementById('japan-result-count');
  const titleEl = document.getElementById('japan-list-title');
  const search = document.getElementById('japan-search');
  const regionChips = document.getElementById('japan-region-chips');
  const levelSwitch = document.getElementById('japan-level-switch');
  const seasonSwitch = document.getElementById('japan-season-switch');
  const seasonBanner = document.getElementById('japan-season-banner');
  const drawer = document.getElementById('japan-drawer');
  const drawerContent = document.getElementById('japan-drawer-content');
  const backdrop = document.getElementById('japan-drawer-backdrop');
  const closeBtn = document.getElementById('japan-drawer-close');
  const stampPop = document.getElementById('passport-stamp-pop');
  const stampName = document.getElementById('passport-stamp-name');
  const visitedCount = document.getElementById('japan-visited-count');
  const passportProgress = document.getElementById('japan-passport-progress');
  const surpriseBtn = document.getElementById('japan-surprise');
  const unvisitedBtn = document.getElementById('japan-show-unvisited');
  const trainToggle = document.getElementById('japan-train-toggle');
  const trainPanel = document.getElementById('japan-train-panel');
  const trainClose = document.getElementById('japan-train-close');
  const trainGrid = document.getElementById('japan-train-route-grid');
  const trainVocab = document.getElementById('japan-train-vocab');
  const passportModal = document.getElementById('japan-passport-modal');
  const passportBackdrop = document.getElementById('japan-passport-backdrop');
  const passportClose = document.getElementById('japan-passport-close');
  const passportStats = document.getElementById('japan-passport-stats');
  const passportRegions = document.getElementById('japan-passport-regions');
  const passportRoutes = document.getElementById('japan-passport-route-progress');
  const passportStamps = document.getElementById('japan-passport-stamp-grid');

  const visited = new Set(window.JAPAN_VISITED || []);
  let activeRegion = 'All';
  let level = localStorage.getItem('kotoba-japan-level') || window.JAPAN_DEFAULT_LEVEL || 'beginner';
  if (!['beginner','intermediate','advanced'].includes(level)) level='beginner';
  let activeSeason = localStorage.getItem('kotoba-japan-season') || 'spring';
  if (!payload.seasons || !payload.seasons[activeSeason]) activeSeason = 'spring';
  let unvisitedOnly = false;
  let selected = null;
  let lastPoint = null;
  let currentWords = [];
  let quizState = null;
  let situationLocked = false;
  let activeTrainRoute = null;
  let routeStopIndex = -1;

  const pinEls = new Map();
  const labelEls = new Map();
  const seenWords = new Set(JSON.parse(sessionStorage.getItem('kotoba-japan-seen-words') || '[]'));

  const geography = window.JAPAN_GEOGRAPHY;
  if (!geography || geography.prefectures?.length !== 47) return;
  const projection = geography.projection;
  const mercator = lat => Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)) * 180 / Math.PI;
  const project = (lon, lat) => ({
    x: projection.left + (lon - projection.west) * projection.scale,
    y: projection.top + (mercator(projection.north) - mercator(lat)) * projection.scale
  });
  const prefectureEls = new Map();
  const overview = new Set(['hokkaido', 'miyagi', 'tokyo', 'aichi', 'osaka', 'hiroshima', 'fukuoka', 'okinawa']);
  let visibleIds = new Set(places.map(p => p.id));
  function svg(tag, attrs = {}) {
    const el = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
    return el;
  }
  geography.surroundingLand.forEach(d => document.getElementById('japan-context-layer').appendChild(svg('path', { d, class: 'jp-context-land' })));
  const grid = document.getElementById('japan-grid-layer');
  for (let lon = 125; lon <= 145; lon += 5) {
    const q = project(lon, 35);
    grid.appendChild(svg('path', { d: `M${q.x},0V920`, class: 'jp-map-grid' }));
    const t = svg('text', { x: q.x + 4, y: 30, class: 'jp-grid-label' }); t.textContent = `${lon}°E`; grid.appendChild(t);
  }
  for (let lat = 25; lat <= 45; lat += 5) {
    const q = project(135, lat);
    grid.appendChild(svg('path', { d: `M0,${q.y}H760`, class: 'jp-map-grid' }));
    const t = svg('text', { x: 8, y: q.y - 5, class: 'jp-grid-label' }); t.textContent = `${lat}°N`; grid.appendChild(t);
  }
  geography.prefectures.forEach(feature => {
    const p = byId.get(feature.id);
    const el = svg('path', { d: feature.path, class: 'jp-prefecture', 'fill-rule': 'evenodd',
      'data-prefecture': feature.id, tabindex: '0', role: 'button', 'aria-label': `${feature.name} prefecture — explore ${p.city_en}` });
    const title = svg('title'); title.textContent = `${p.prefecture_jp} · ${feature.name}`; el.appendChild(title);
    el.addEventListener('click', () => selectPlace(p));
    el.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); selectPlace(p); } });
    islands.appendChild(el); prefectureEls.set(feature.id, el);
  });
  const geographicLabels = [
    [133.3, 40.1, 'Sea of Japan', '日本海', 'sea'], [142.6, 32.2, 'Pacific Ocean', '太平洋', 'sea'],
    [125.6, 29.9, 'East China Sea', '東シナ海', 'sea'], [144.2, 46.0, 'Sea of Okhotsk', '', 'sea'],
    [139.5, 44.0, 'Hokkaidō', '北海道', 'island'], [143.3, 37.4, 'Honshū', '本州', 'island'],
    [133.5, 32.4, 'Shikoku', '四国', 'island'], [128.3, 31.6, 'Kyūshū', '九州', 'island'],
    [125.9, 27.0, 'Ryūkyū Islands', '琉球諸島', 'island'],
    [133.1, 45.4, 'RUSSIA', '', 'country'], [127.8, 36.4, 'SOUTH KOREA', '', 'country'],
    [126.4, 40.2, 'NORTH KOREA', '', 'country']
  ];
  const geoLabelEls = [];
  geographicLabels.forEach(([lon, lat, name, jp, type]) => {
    const q = project(lon, lat), el = svg('text', { x: q.x, y: q.y, class: type === 'country' ? 'jp-country-label' : 'jp-geographic-label' });
    el.appendChild(document.createTextNode(name));
    if (jp) { const small = svg('tspan', { x: q.x, dy: '1.45em' }); small.textContent = jp; el.appendChild(small); }
    document.getElementById('japan-geographic-labels').appendChild(el); geoLabelEls.push({ el, type });
  });

  function nearestPin(event, fallback) {
    const matrix = map.getScreenCTM(); if (!matrix) return fallback;
    let nearest = fallback, best = 22;
    places.forEach(p => {
      const g = pinEls.get(p.id);
      if (!visibleIds.has(p.id) || g.classList.contains('overview-dot')) return;
      const q = project(p.lon, p.lat), screen = new DOMPoint(q.x, q.y).matrixTransform(matrix);
      const distance = Math.hypot(screen.x - event.clientX, screen.y - event.clientY);
      if (distance < best) { best = distance; nearest = p; }
    });
    return nearest;
  }

  places.forEach(place => {
    const q = project(place.lon, place.lat);
    const g = svg('g', { class: `jp-map-pin ${visited.has(place.id) ? 'visited' : ''}`, 'data-place': place.id,
      tabindex: '0', role: 'button', 'aria-label': `${place.city_en}, ${place.prefecture_en}` });
    const pulse = svg('circle', { cx: q.x, cy: q.y, r: 10, class: 'jp-pin-pulse' });
    const dot = svg('circle', { cx: q.x, cy: q.y, r: 4, class: 'jp-pin-dot' });
    const hit = svg('circle', { cx: q.x, cy: q.y, r: 16, class: 'jp-pin-hit' });
    const title = svg('title'); title.textContent = `${place.city_en} · ${place.prefecture_en}`;
    g.append(pulse, dot, hit, title); pinLayer.appendChild(g); pinEls.set(place.id, g);
    g.addEventListener('click', event => selectPlace(nearestPin(event, place)));
    g.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); selectPlace(place); } });
    const text = svg('text', { x: q.x + 8, y: q.y - 6, class: 'jp-capital-label' });
    text.textContent = place.city_en; labelLayer.appendChild(text); labelEls.set(place.id, text);
  });

  function updateMapView(view) {
    const scale = map.getScreenCTM()?.a || 1;
    const accepted = [];
    const ordered = [...places].sort((a, b) => Number(b.id === selected?.id) - Number(a.id === selected?.id) || Number(overview.has(b.id)) - Number(overview.has(a.id)));
    ordered.forEach(p => {
      const q = project(p.lon, p.lat), g = pinEls.get(p.id), text = labelEls.get(p.id);
      const detail = view.zoom >= 1.8 || overview.has(p.id) || p.id === selected?.id;
      g.classList.toggle('overview-dot', !detail);
      g.style.setProperty('--pin-radius', `${(p.id === selected?.id ? 5 : detail ? 3.6 : 1.8) / scale}px`);
      g.querySelector('.jp-pin-hit').setAttribute('r', (detail ? view.zoom >= 1.8 ? 20 : 11 : 2) / scale);
      g.querySelector('.jp-pin-pulse').setAttribute('r', 10 / scale);
      g.setAttribute('tabindex', visibleIds.has(p.id) && detail ? '0' : '-1');
      g.setAttribute('aria-hidden', String(!visibleIds.has(p.id) || !detail));
      text.style.visibility = 'hidden'; text.style.fontSize = `${12 / scale}px`;
      if (!visibleIds.has(p.id) || !detail || q.x < view.x || q.x > view.x + view.width || q.y < view.y || q.y > view.y + view.height) return;
      const width = p.city_en.length * 6.8 / scale, height = 15 / scale;
      const candidates = [[q.x + 8 / scale, q.y - 6 / scale], [q.x + 8 / scale, q.y + 16 / scale], [q.x - width - 8 / scale, q.y - 6 / scale]];
      for (const [x, y] of candidates) {
        const box = { x, y: y - height, w: width, h: height + 3 / scale };
        if (box.x < view.x + 4 / scale || box.x + box.w > view.x + view.width - 4 / scale || box.y < view.y || box.y + box.h > view.y + view.height) continue;
        if (accepted.some(b => box.x < b.x + b.w && box.x + box.w > b.x && box.y < b.y + b.h && box.y + box.h > b.y)) continue;
        text.setAttribute('x', x); text.setAttribute('y', y); text.style.visibility = 'visible'; accepted.push(box); break;
      }
    });
    geoLabelEls.forEach(({ el, type }) => {
      el.style.fontSize = `${(type === 'country' ? 9 : 12) / scale}px`;
      el.querySelector('tspan')?.style.setProperty('font-size', `${9 / scale}px`);
      el.style.opacity = view.zoom > 3 ? '.55' : '1';
    });
    grid.querySelectorAll('text').forEach(el => el.style.fontSize = `${9 / scale}px`);
    routeLayer?.querySelectorAll('.jp-route-stop').forEach(el => el.setAttribute('r', 4 / scale));
    const centerMercator = mercator(projection.north) - (view.y + view.height / 2 - projection.top) / projection.scale;
    const latitude = Math.atan(Math.sinh(centerMercator * Math.PI / 180));
    const kmPerPixel = 111.195 * Math.cos(latitude) / projection.scale / scale;
    const desiredKm = 95 * kmPerPixel, magnitude = Math.pow(10, Math.floor(Math.log10(desiredKm)));
    const distance = [1, 2, 5, 10].map(x => x * magnitude).filter(x => x <= desiredKm).pop() || magnitude;
    document.getElementById('japan-map-scale-label').textContent = `${distance} km`;
    document.getElementById('japan-map-scale-bar').style.width = `${distance / kmPerPixel}px`;
  }
  const camera = window.KotobaJapanMap(map, { onChange: updateMapView });
  new ResizeObserver(() => updateMapView(camera.getView())).observe(map);
  function focusPlaces(rows) {
    if (!rows.length) return;
    if (rows.length === 47) { camera.reset(); return; }
    if (rows.length === 1 && rows[0].id === 'hokkaido' && activeRegion === 'Hokkaido') {
      camera.fit(geography.prefectures.find(f => f.id === 'hokkaido').bounds, 25); return;
    }
    const points = rows.map(p => project(p.lon, p.lat));
    camera.fit([Math.min(...points.map(p => p.x)), Math.min(...points.map(p => p.y)), Math.max(...points.map(p => p.x)), Math.max(...points.map(p => p.y))], 42, 4.5);
  }

  function esc(v){ return String(v??'').replace(/[&<>'"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[m])); }
  function normalize(v){ return String(v||'').toLowerCase().normalize('NFKC'); }
  function shuffle(a){ const b=[...a]; for(let i=b.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[b[i],b[j]]=[b[j],b[i]];} return b; }
  function levelLabel(){ return level[0].toUpperCase()+level.slice(1); }
  function placeImage(place,idx){ return `/static/images/japan_explorer/${place.id}-${idx}.svg`; }
  function countRouteVisited(route){ return route.stops.filter(id=>visited.has(id)).length; }

  function setLevel(next){
    level=next; localStorage.setItem('kotoba-japan-level',level);
    levelSwitch.querySelectorAll('button').forEach(b=>b.classList.toggle('active',b.dataset.level===level));
    if(selected) renderDrawer(selected,false);
  }
  levelSwitch.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>setLevel(b.dataset.level)));
  setLevel(level);

  function seasonRecommended(place){
    const s=payload.seasons && payload.seasons[activeSeason];
    return !!(s && Array.isArray(s.recommended) && s.recommended.includes(place.id));
  }

  function renderSeasonDecor(){
    // Seasonal palettes and featured pins keep the geographic map uncluttered.
    if(seasonLayer) seasonLayer.innerHTML='';
    document.getElementById('japan-map-wrap')?.setAttribute('data-season',activeSeason);
  }

  function setSeason(next){
    if(!payload.seasons || !payload.seasons[next]) return;
    activeSeason=next; localStorage.setItem('kotoba-japan-season',activeSeason);
    seasonSwitch.querySelectorAll('button').forEach(b=>b.classList.toggle('active',b.dataset.season===activeSeason));
    const s=payload.seasons[activeSeason];
    const oceanColors={spring:['#bedbea','#9bbfd6'],summer:['#b4dce8','#8cbacf'],autumn:['#c8dce6','#a4bdd0'],winter:['#cbdfe9','#a9c5d8']}[activeSeason]||['#dff6ff','#9edcf0'];
    const landColors={spring:['#fffcef','#e8e3c4'],summer:['#f6fae5','#dbe5bf'],autumn:['#fff7e7','#e9d6b0'],winter:['#fbfcf3','#e0e8de']}[activeSeason]||['#dfe9c7','#6fae7c'];
    const oceanStops=document.querySelectorAll('#jp-ocean stop'); if(oceanStops[0])oceanStops[0].setAttribute('stop-color',oceanColors[0]); if(oceanStops[1])oceanStops[1].setAttribute('stop-color',oceanColors[1]);
    const landStops=document.querySelectorAll('#jp-land stop'); if(landStops[0])landStops[0].setAttribute('stop-color',landColors[0]); if(landStops[2])landStops[2].setAttribute('stop-color',landColors[1]);
    seasonBanner.innerHTML=`<div class="japan-season-banner-icon">${esc(s.icon)}</div><div><strong>${esc(s.jp)} · ${esc(s.label)} spotlight</strong><span>${esc(s.tagline)}</span></div><button class="btn-ghost" type="button" id="japan-season-only">Show highlighted places</button>`;
    document.getElementById('japan-season-only').onclick=()=>{
      activeRegion='All'; regionChips.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x.dataset.region==='All'));
      search.value=''; unvisitedOnly=false; unvisitedBtn.classList.remove('active'); unvisitedBtn.textContent='Show unvisited';
      const featured=places.filter(p=>seasonRecommended(p));
      visibleIds=new Set(featured.map(p=>p.id));
      renderList(featured); focusPlaces(featured);
      places.forEach(p=>{ const show=seasonRecommended(p); pinEls.get(p.id)?.classList.toggle('filtered-out',!show); labelEls.get(p.id)?.classList.toggle('filtered-out',!show); });
      prefectureEls.forEach((el,id)=>{const show=visibleIds.has(id);el.classList.toggle('filtered-out',!show);el.setAttribute('tabindex',show?'0':'-1');el.setAttribute('aria-hidden',String(!show));});
      updateMapView(camera.getView());
      countEl.textContent=places.filter(seasonRecommended).length; titleEl.textContent=`${s.label} highlights`;
    };
    places.forEach(p=>pinEls.get(p.id)?.classList.toggle('season-featured',seasonRecommended(p)));
    renderSeasonDecor();
    if(selected) renderDrawer(selected,false);
  }
  seasonSwitch.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>setSeason(b.dataset.season)));
  setSeason(activeSeason);

  (payload.regions||[]).forEach(region=>{
    const b=document.createElement('button'); b.type='button'; b.dataset.region=region; b.textContent=region; regionChips.appendChild(b);
  });
  regionChips.addEventListener('click',e=>{
    const b=e.target.closest('[data-region]'); if(!b)return;
    activeRegion=b.dataset.region; regionChips.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b)); applyFilters(true);
  });
  search.addEventListener('input',()=>applyFilters(true));

  function matches(place){
    if(activeRegion!=='All' && place.region!==activeRegion) return false;
    if(unvisitedOnly && visited.has(place.id)) return false;
    const q=normalize(search.value).trim(); if(!q)return true;
    const dialect=(payload.dialects||{})[place.region]||{};
    const hay=normalize([place.prefecture_en,place.prefecture_jp,place.city_en,place.city_jp,place.reading,place.region,...place.famous,...place.foods,dialect.jp,dialect.en].join(' '));
    return KotobaSearchMatch.matches(hay, q);
  }

  function applyFilters(focus=false){
    const filtered=places.filter(matches);
    renderList(filtered); countEl.textContent=filtered.length;
    titleEl.textContent=search.value.trim()?`Results for “${search.value.trim()}”`:(activeRegion==='All'?(unvisitedOnly?'Unvisited places':'All 47'):`${activeRegion}${unvisitedOnly?' · unvisited':''}`);
    const ids=new Set(filtered.map(x=>x.id)); visibleIds=ids;
    places.forEach(p=>{
      const show=ids.has(p.id), pin=pinEls.get(p.id), label=labelEls.get(p.id);
      if(pin){pin.classList.toggle('filtered-out',!show);pin.setAttribute('aria-hidden',show?'false':'true');}
      if(label) label.classList.toggle('filtered-out',!show);
      const area=prefectureEls.get(p.id); area?.classList.toggle('filtered-out',!show); area?.setAttribute('tabindex',show?'0':'-1'); area?.setAttribute('aria-hidden',String(!show));
    });
    if(focus) focusPlaces(filtered);
    updateMapView(camera.getView());
  }

  function renderList(rows){
    list.innerHTML='';
    rows.forEach((p,i)=>{
      const card=document.createElement('button'); card.type='button'; card.className=`japan-place-card ${visited.has(p.id)?'visited':''} ${seasonRecommended(p)?'season-card':''}`; card.style.setProperty('--delay',`${Math.min(i,18)*18}ms`);
      card.innerHTML=`<span class="japan-place-code">${String(p.code).padStart(2,'0')}</span><span class="japan-place-copy"><strong>${esc(p.city_en)}</strong><small>${esc(p.city_jp)} · ${esc(p.prefecture_en)}</small><em>${esc(p.tagline)}</em></span><span class="japan-place-status">${visited.has(p.id)?'✓':seasonRecommended(p)?(payload.seasons[activeSeason]?.icon||'•'):'›'}</span>`;
      card.addEventListener('click',()=>selectPlace(p)); list.appendChild(card);
    });
    if(!rows.length) list.innerHTML='<div class="japan-empty"><strong>No matching place</strong><span>Try another city, prefecture, or region.</span></div>';
  }

  function pickWords(place){
    const specific=(place.level_words && place.level_words[level])||[];
    const pool=(payload.common_words && payload.common_words[level])||[];
    const words=[]; specific.forEach(w=>{if(!words.some(x=>x.jp===w.jp))words.push({...w,local:true});});
    let candidates=shuffle(pool.filter(w=>!seenWords.has(`${level}:${w.jp}`))); if(candidates.length<4)candidates=shuffle(pool);
    for(const w of candidates){if(words.length>=5)break;if(!words.some(x=>x.jp===w.jp))words.push({...w,local:false});}
    currentWords=words.slice(0,5); currentWords.forEach(w=>seenWords.add(`${level}:${w.jp}`));
    sessionStorage.setItem('kotoba-japan-seen-words',JSON.stringify([...seenWords].slice(-100))); return currentWords;
  }

  function renderDialect(place){
    const d=(payload.dialects||{})[place.region]; if(!d)return '';
    return `<section class="japan-dialect-card"><div class="japan-section-title"><div><p class="hero-eyebrow">方言 — dialect corner</p><h3>A regional expression</h3></div><span class="japan-dialect-badge">${esc(place.region)}</span></div><div class="japan-dialect-main"><div><ruby>${esc(d.jp)}<rt>${esc(d.reading)}</rt></ruby><strong>${esc(d.en)}</strong></div><button class="speak-btn" type="button" data-speak="${esc(d.jp)}" data-reading="${esc(d.reading)}">🔊 Hear it</button></div><p class="japan-dialect-example"><ruby>${esc(d.example)}<rt>${esc(d.example_reading)}</rt></ruby><span>${esc(d.example_en)}</span></p><small>${esc(d.note)}</small></section>`;
  }

  function renderSituation(place){
    const s=(place.situations||{})[level]; if(!s)return '';
    const opts=shuffle(s.options||[]).map(o=>`<button type="button" data-situation-answer="${esc(o)}">${esc(o)}</button>`).join('');
    return `<section class="japan-situation-card"><div class="japan-section-title"><div><p class="hero-eyebrow">実戦 — real-life Japanese</p><h3>${esc(s.title)}</h3></div><span class="japan-level-badge">${levelLabel()}</span></div><p class="japan-situation-scene">${esc(s.scene)}</p><strong class="japan-situation-prompt">${esc(s.prompt)}</strong><div class="japan-situation-options">${opts}</div><div class="japan-situation-feedback" id="japan-situation-feedback"></div></section>`;
  }

  function activeRoutePosition(place){
    if(!activeTrainRoute)return null; const idx=activeTrainRoute.stops.indexOf(place.id); if(idx<0)return null;
    return {idx,total:activeTrainRoute.stops.length};
  }

  function renderDrawer(place,markVisit=true){
    currentWords=pickWords(place); situationLocked=false;
    const phrase=(place.phrases||{})[level]||{};
    const words=currentWords.map((w,i)=>`<article class="japan-word-card ${w.local?'local-word':''}"><div><span class="word-number">${i+1}</span>${w.local?'<span class="local-word-badge">LOCAL</span>':''}</div><ruby class="japan-word-ruby">${esc(w.jp)}<rt>${esc(w.reading)}</rt></ruby><span>${esc(w.en)}</span><div class="japan-word-actions"><button class="line-speak" type="button" data-speak="${esc(w.jp)}" data-reading="${esc(w.reading)}">🔊</button><button class="favorite-btn" type="button" data-favorite-kind="japan-word" data-favorite-id="${esc(place.id+':'+w.jp)}" data-favorite-front="${esc(w.jp)}" data-favorite-reading="${esc(w.reading)}" data-favorite-meaning="${esc(w.en)}" data-favorite-list="Japan Explorer">☆ Save</button></div></article>`).join('');
    const gallery=(place.visuals||[]).map((v,i)=>`<figure class="japan-gallery-card"><img src="${placeImage(place,i+1)}" alt="Illustrated ${esc(place.prefecture_en)} learning postcard: ${esc(v.title)}"><figcaption><strong>${esc(v.title)}</strong><span>${esc(v.caption)}</span></figcaption></figure>`).join('');
    const famous=(place.famous||[]).map(x=>`<li>${esc(x)}</li>`).join('');
    const foods=(place.foods||[]).map(x=>`<span>${esc(x)}</span>`).join('');
    const seasonNames=(place.best_seasons||[]).map(k=>payload.seasons?.[k]?.icon+' '+payload.seasons?.[k]?.label).filter(Boolean).join(' · ');
    const routePos=activeRoutePosition(place);
    const routeBar=routePos?`<div class="japan-active-route"><span>${esc(activeTrainRoute.icon)} ${esc(activeTrainRoute.name)}</span><strong>Stop ${routePos.idx+1} / ${routePos.total}</strong>${routePos.idx<routePos.total-1?'<button type="button" id="japan-next-train-stop">Next stop →</button>':'<em>Route complete 🎉</em>'}</div>`:'';
    drawerContent.innerHTML=`<div class="japan-detail-hero"><img src="${placeImage(place,1)}" alt="Illustrated postcard for ${esc(place.prefecture_en)}"><div class="japan-detail-overlay"><span class="japan-region-pill">${esc(place.region)}</span><span class="japan-season-pill">${esc(seasonNames||'Year-round')}</span><span class="japan-visited-pill ${visited.has(place.id)?'shown':''}">✓ Passport stamp</span></div></div><div class="japan-detail-body">${routeBar}<div class="japan-detail-title-row"><div><p class="hero-eyebrow">${esc(place.prefecture_jp)} · ${esc(place.prefecture_en)}</p><h2>${esc(place.city_en)} <small>${esc(place.city_jp)}</small></h2><p class="japan-reading">${esc(place.reading)}</p></div><button class="speak-btn" type="button" data-speak="${esc(place.city_jp)}" data-reading="${esc(place.reading)}">🔊 Hear it</button></div><p class="japan-tagline">${esc(place.tagline)}</p><p class="japan-description">${esc(place.description)}</p><div class="japan-fact-grid"><div><span>Famous for</span><ul>${famous}</ul></div><div><span>Local tastes</span><div class="japan-food-tags">${foods}</div></div></div><section class="japan-gallery-section"><div class="japan-section-title"><div><p class="hero-eyebrow">見る — remember visually</p><h3>Location postcards</h3></div><small>Offline illustrations</small></div><div class="japan-gallery">${gallery}</div></section>${renderDialect(place)}${renderSituation(place)}<section class="japan-lesson-section"><div class="japan-section-title"><div><p class="hero-eyebrow">ことば — words</p><h3>Your ${levelLabel()} five</h3></div><span class="japan-level-badge">${levelLabel()}</span></div><p class="japan-lesson-note">One local term + fresh travel Japanese. Kotoba avoids repeating generic map words during this session until the pool needs to recycle.</p><div class="japan-word-grid">${words}</div><article class="japan-phrase-card"><span>Phrase for this stop</span><ruby class="japan-phrase-ruby">${esc(phrase.jp||'')}<rt>${esc(phrase.reading||'')}</rt></ruby><p>${esc(phrase.en||'')}</p><button class="speak-btn" type="button" data-speak="${esc(phrase.jp||'')}" data-reading="${esc(phrase.reading||'')}">🔊 Listen</button></article><div class="japan-lesson-actions"><button class="btn-primary" id="japan-start-quiz" type="button">Mini quiz · 3 questions</button><button class="favorite-btn" type="button" data-favorite-kind="japan-place" data-favorite-id="${esc(place.id)}" data-favorite-front="${esc(place.city_jp)}" data-favorite-reading="${esc(place.reading)}" data-favorite-meaning="${esc(place.tagline)}" data-favorite-list="Japan Explorer">☆ Save place</button></div><div id="japan-mini-quiz" class="japan-mini-quiz" hidden></div></section></div>`;
    drawer.classList.add('open'); drawer.setAttribute('aria-hidden','false'); backdrop.hidden=false; requestAnimationFrame(()=>backdrop.classList.add('show')); document.body.classList.add('japan-drawer-open');
    if(window.KotobaSpeech) KotobaSpeech.wire(drawerContent); if(window.KotobaLearn) KotobaLearn.wireFavorites(drawerContent);
    document.getElementById('japan-start-quiz')?.addEventListener('click',startMiniQuiz);
    drawerContent.querySelectorAll('[data-situation-answer]').forEach(btn=>btn.addEventListener('click',()=>answerSituation(btn,place)));
    document.getElementById('japan-next-train-stop')?.addEventListener('click',()=>goNextTrainStop());
    if(markVisit) markVisited(place);
  }

  async function answerSituation(btn,place){
    if(situationLocked)return; situationLocked=true;
    const s=(place.situations||{})[level]; if(!s)return;
    const correct=btn.dataset.situationAnswer===s.correct;
    drawerContent.querySelectorAll('[data-situation-answer]').forEach(b=>{b.disabled=true;if(b.dataset.situationAnswer===s.correct)b.classList.add('correct');else if(b===btn)b.classList.add('wrong');});
    const feedback=document.getElementById('japan-situation-feedback');
    feedback.innerHTML=`<strong>${correct?'✓ Nice!':'Try this phrase instead'}</strong><ruby>${esc(s.correct)}<rt>${esc(s.reading||'')}</rt></ruby><span>${esc(s.en||'')}</span><button class="line-speak" type="button" data-speak="${esc(s.correct)}" data-reading="${esc(s.reading||'')}">🔊 Listen</button>`;
    if(window.KotobaSpeech)KotobaSpeech.wire(feedback);
    if(window.KotobaLearn){await KotobaLearn.record({kind:'japan-situation',id:`${place.id}:${level}:${s.title}`,front:s.scene,prompt:s.prompt,answer:s.correct,chosen:btn.dataset.situationAnswer,correct,quality:correct?4:1,reading:s.reading,meaning:s.en,level:levelLabel(),sub:`Japan Explorer · ${place.prefecture_en}`,explanation:`${s.correct}（${s.reading}） — ${s.en}`});}
  }

  function movePlane(place){
    const q=project(place.lon,place.lat);
    if(!lastPoint){plane.style.transition='none';plane.style.transform=`translate(${q.x}px,${q.y}px)`;requestAnimationFrame(()=>plane.style.transition='transform .85s cubic-bezier(.2,.75,.25,1)');lastPoint=q;return;}
    const ang=Math.atan2(q.y-lastPoint.y,q.x-lastPoint.x)*180/Math.PI; plane.style.setProperty('--plane-angle',`${ang}deg`);plane.classList.add('flying');plane.style.transform=`translate(${q.x}px,${q.y}px) rotate(${ang}deg)`;clearTimeout(plane._t);plane._t=setTimeout(()=>plane.classList.remove('flying'),900);lastPoint=q;
  }

  function moveTrain(place){
    if(!train||!activeTrainRoute)return; const q=project(place.lon,place.lat); train.style.opacity='1'; train.classList.add('moving'); train.style.transform=`translate(${q.x}px,${q.y}px)`; clearTimeout(train._t); train._t=setTimeout(()=>train.classList.remove('moving'),900);
  }

  function selectPlace(place){
    if(document.getElementById('japan-map-wrap').classList.contains('is-expanded'))camera.setExpanded(false);
    selected=place;
    const point=project(place.lon,place.lat), view=camera.getView();
    if(view.zoom<2 || point.x<view.x || point.x>view.x+view.width || point.y<view.y || point.y>view.y+view.height)camera.fit([point.x,point.y,point.x,point.y],45,3.5);
    prefectureEls.forEach((el,id)=>el.classList.toggle('selected',id===place.id));
    updateMapView(camera.getView());
    if(activeTrainRoute && activeTrainRoute.stops.includes(place.id)){routeStopIndex=activeTrainRoute.stops.indexOf(place.id);moveTrain(place);}else movePlane(place);
    pinEls.forEach((g,id)=>g.classList.toggle('selected',id===place.id)); renderDrawer(place,true);
    const card=[...list.querySelectorAll('.japan-place-card')].find(c=>c.querySelector('strong')?.textContent===place.city_en); if(card)card.scrollIntoView({block:'nearest',behavior:'smooth'});
  }

  function closeDrawer(){drawer.classList.remove('open');drawer.setAttribute('aria-hidden','true');backdrop.classList.remove('show');document.body.classList.remove('japan-drawer-open');setTimeout(()=>backdrop.hidden=true,220);}
  closeBtn.addEventListener('click',closeDrawer); backdrop.addEventListener('click',closeDrawer); document.addEventListener('keydown',e=>{if(e.key==='Escape'&&drawer.classList.contains('open'))closeDrawer();if(e.key==='Escape'&&!passportModal.hidden)closePassport();});

  async function markVisited(place){
    try{
      const r=await fetch('/api/japan/visit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:place.id})}); if(!r.ok)return; const d=await r.json();
      if(d.visited_ids){visited.clear();d.visited_ids.forEach(x=>visited.add(x));}
      pinEls.get(place.id)?.classList.add('visited'); visitedCount.textContent=d.visited_count??visited.size; passportProgress.style.width=`${Math.round(100*(d.visited_count??visited.size)/47)}%`; applyFilters(); refreshTrainCards();
      const vp=drawerContent.querySelector('.japan-visited-pill');if(vp)vp.classList.add('shown');
      if(d.first_time){showStamp(place);if(window.KotobaLearn)KotobaLearn.toast(`Passport stamp: ${place.prefecture_en} · +${d.xp_awarded||12} XP`);}
      if(!passportModal.hidden)renderPassport();
    }catch(_){ }
  }

  function showStamp(place){stampName.textContent=`${place.prefecture_en} explored!`;stampPop.hidden=false;stampPop.classList.remove('play');void stampPop.offsetWidth;stampPop.classList.add('play');clearTimeout(stampPop._t);stampPop._t=setTimeout(()=>{stampPop.classList.remove('play');stampPop.hidden=true;},1800);}

  function startMiniQuiz(){const targetWords=shuffle(currentWords).slice(0,3);quizState={idx:0,score:0,words:targetWords};const box=document.getElementById('japan-mini-quiz');if(!box)return;box.hidden=false;renderQuizQuestion();requestAnimationFrame(()=>box.scrollIntoView({behavior:'smooth',block:'start',inline:'nearest'}));}
  function renderQuizQuestion(){
    const box=document.getElementById('japan-mini-quiz');if(!box||!quizState)return;
    if(quizState.idx>=quizState.words.length){box.innerHTML=`<div class="japan-quiz-finish"><span>旅</span><h4>${quizState.score} / ${quizState.words.length}</h4><p>${quizState.score===quizState.words.length?'Perfect stop! These words are now in your learning history.':'Good practice. Any miss is now available in your Mistake Notebook and Smart Review.'}</p><button type="button" class="btn-ghost" id="japan-quiz-again">Quiz again</button></div>`;document.getElementById('japan-quiz-again').onclick=startMiniQuiz;return;}
    const word=quizState.words[quizState.idx];const all=[...currentWords,...((payload.common_words||{})[level]||[])];const distract=shuffle(all.filter(w=>w.en!==word.en&&w.jp!==word.jp)).slice(0,3).map(w=>w.en);const options=shuffle([word.en,...distract]);
    box.innerHTML=`<div class="japan-quiz-head"><span>${quizState.idx+1} / ${quizState.words.length}</span><strong>What does this mean?</strong></div><div class="japan-quiz-prompt">${esc(word.jp)}<small>${esc(word.reading)}</small></div><div class="japan-quiz-options">${options.map(o=>`<button type="button" data-answer="${esc(o)}">${esc(o)}</button>`).join('')}</div><div class="japan-quiz-feedback" id="japan-quiz-feedback"></div>`;box.querySelectorAll('[data-answer]').forEach(btn=>btn.addEventListener('click',()=>answerQuiz(btn,word)));
  }
  async function answerQuiz(btn,word){
    const box=document.getElementById('japan-mini-quiz');if(!box||box.dataset.locked==='1')return;box.dataset.locked='1';const correct=btn.dataset.answer===word.en;if(correct)quizState.score++;
    box.querySelectorAll('[data-answer]').forEach(b=>{b.disabled=true;if(b.dataset.answer===word.en)b.classList.add('correct');else if(b===btn)b.classList.add('wrong')});const feedback=document.getElementById('japan-quiz-feedback');feedback.innerHTML=`<strong>${correct?'✓ Correct':'Not quite'}</strong><span>${esc(word.jp)}（${esc(word.reading)}）— ${esc(word.en)}</span>`;
    if(window.KotobaLearn)await KotobaLearn.record({kind:'japan-word',id:`${selected.id}:${word.jp}`,front:word.jp,reading:word.reading,meaning:word.en,answer:word.en,correct,chosen:btn.dataset.answer,level:levelLabel(),sub:`Japan Explorer · ${selected.prefecture_en}`,explanation:`${word.jp}（${word.reading}） means “${word.en}”. You met it while exploring ${selected.prefecture_en}.`});
    setTimeout(()=>{quizState.idx++;box.dataset.locked='0';renderQuizQuestion();},900);
  }

  function drawTrainRoute(route){
    routeLayer.innerHTML=''; if(!route)return;
    const points=route.stops.map(id=>byId.get(id)).filter(Boolean).map(p=>project(p.lon,p.lat)); if(points.length<2)return;
    const poly=svg('polyline',{points:points.map(q=>`${q.x},${q.y}`).join(' '),class:'jp-train-route-line'});routeLayer.appendChild(poly);
    points.forEach((q,i)=>{const c=svg('circle',{cx:q.x,cy:q.y,r:8,class:`jp-route-stop ${visited.has(route.stops[i])?'done':''}`});routeLayer.appendChild(c);});
    updateMapView(camera.getView());
  }

  function refreshTrainCards(){
    trainGrid.innerHTML=''; (payload.train_routes||[]).forEach(route=>{
      const done=countRouteVisited(route), total=route.stops.length, pct=Math.round(100*done/total), active=activeTrainRoute?.id===route.id;
      const names=route.stops.map(id=>byId.get(id)?.city_en).filter(Boolean).join(' → ');
      const card=document.createElement('article');card.className=`japan-train-route-card ${active?'active':''}`;card.innerHTML=`<div class="japan-train-card-top"><span>${esc(route.icon)}</span><div><strong>${esc(route.name)}</strong><small>${esc(route.jp)}</small></div><b>${done}/${total}</b></div><p>${esc(route.description)}</p><div class="japan-train-stops">${esc(names)}</div><div class="japan-route-track"><i style="width:${pct}%"></i></div><button type="button" class="${active?'btn-primary':'btn-ghost'}" data-train-route="${esc(route.id)}">${active?'Continue route':'Start journey'}</button>`;trainGrid.appendChild(card);
    });
    trainGrid.querySelectorAll('[data-train-route]').forEach(b=>b.addEventListener('click',()=>startTrainRoute(b.dataset.trainRoute)));
    trainVocab.innerHTML=`<div><p class="hero-eyebrow">駅のことば — station words</p><h3>Useful train Japanese</h3></div><div class="japan-train-word-row">${(payload.train_vocab||[]).map(w=>`<button type="button" data-speak="${esc(w.jp)}" data-reading="${esc(w.reading)}"><ruby>${esc(w.jp)}<rt>${esc(w.reading)}</rt></ruby><span>${esc(w.en)}</span></button>`).join('')}</div>`;
    if(window.KotobaSpeech)KotobaSpeech.wire(trainVocab);
  }

  function startTrainRoute(id){
    const route=(payload.train_routes||[]).find(r=>r.id===id); if(!route)return; activeTrainRoute=route; localStorage.setItem('kotoba-japan-train-route',id); drawTrainRoute(route); refreshTrainCards();
    routeStopIndex=route.stops.findIndex(pid=>!visited.has(pid)); if(routeStopIndex<0)routeStopIndex=0;
    const p=byId.get(route.stops[routeStopIndex]); if(p){selectPlace(p); map?.scrollIntoView({behavior:'smooth',block:'center'});}
  }
  function goNextTrainStop(){if(!activeTrainRoute)return;routeStopIndex=Math.min(routeStopIndex+1,activeTrainRoute.stops.length-1);const p=byId.get(activeTrainRoute.stops[routeStopIndex]);if(p)selectPlace(p);}

  trainToggle?.addEventListener('click',()=>{trainPanel.hidden=false;refreshTrainCards();trainPanel.scrollIntoView({behavior:'smooth',block:'start'});});
  trainClose?.addEventListener('click',()=>{trainPanel.hidden=true;});
  const rememberedRoute=localStorage.getItem('kotoba-japan-train-route'); if(rememberedRoute){activeTrainRoute=(payload.train_routes||[]).find(r=>r.id===rememberedRoute)||null;if(activeTrainRoute)drawTrainRoute(activeTrainRoute);}
  refreshTrainCards();

  function renderPassport(){
    const regionRows=(payload.regions||[]).map(region=>{const rows=places.filter(p=>p.region===region), done=rows.filter(p=>visited.has(p.id)).length;return {region,done,total:rows.length};});
    const completedRegions=regionRows.filter(r=>r.done===r.total).length;
    const completedRoutes=(payload.train_routes||[]).filter(r=>countRouteVisited(r)===r.stops.length).length;
    passportStats.innerHTML=`<div><strong>${visited.size}</strong><span>Prefectures stamped</span></div><div><strong>${completedRegions}</strong><span>Regions completed</span></div><div><strong>${completedRoutes}</strong><span>Train journeys completed</span></div><div><strong>${47-visited.size}</strong><span>Places still waiting</span></div>`;
    passportRegions.innerHTML=`<div class="japan-passport-section-title"><h3>Region progress</h3><span>${completedRegions} / ${regionRows.length} complete</span></div><div class="japan-passport-region-grid">${regionRows.map(r=>`<article class="${r.done===r.total?'complete':''}"><div><strong>${esc(r.region)}</strong><span>${r.done}/${r.total}</span></div><div class="japan-route-track"><i style="width:${Math.round(100*r.done/r.total)}%"></i></div></article>`).join('')}</div>`;
    passportRoutes.innerHTML=`<div class="japan-passport-section-title"><h3>Train journey stamps</h3><span>${completedRoutes} / ${(payload.train_routes||[]).length} complete</span></div><div class="japan-passport-train-grid">${(payload.train_routes||[]).map(r=>{const d=countRouteVisited(r),all=d===r.stops.length;return `<button type="button" data-passport-route="${esc(r.id)}" class="${all?'complete':''}"><span>${esc(r.icon)}</span><strong>${esc(r.name)}</strong><small>${d}/${r.stops.length} stops ${all?'· COMPLETE':''}</small></button>`}).join('')}</div>`;
    passportStamps.innerHTML=places.map(p=>`<button type="button" data-passport-place="${esc(p.id)}" class="japan-passport-stamp ${visited.has(p.id)?'stamped':''}"><span>${visited.has(p.id)?'済':'?'}</span><strong>${esc(p.prefecture_jp)}</strong><small>${esc(p.prefecture_en)}</small></button>`).join('');
    passportStamps.querySelectorAll('[data-passport-place]').forEach(b=>b.addEventListener('click',()=>{closePassport();selectPlace(byId.get(b.dataset.passportPlace));}));
    passportRoutes.querySelectorAll('[data-passport-route]').forEach(b=>b.addEventListener('click',()=>{closePassport();trainPanel.hidden=false;startTrainRoute(b.dataset.passportRoute);}));
  }
  function openPassport(){renderPassport();passportModal.hidden=false;passportBackdrop.hidden=false;passportModal.setAttribute('aria-hidden','false');document.body.classList.add('japan-passport-open');requestAnimationFrame(()=>{passportModal.classList.add('open');passportBackdrop.classList.add('show');});}
  function closePassport(){passportModal.classList.remove('open');passportBackdrop.classList.remove('show');passportModal.setAttribute('aria-hidden','true');document.body.classList.remove('japan-passport-open');setTimeout(()=>{passportModal.hidden=true;passportBackdrop.hidden=true;},220);}
  document.getElementById('japan-open-passport')?.addEventListener('click',openPassport); document.getElementById('japan-open-passport-card')?.addEventListener('click',openPassport); passportClose?.addEventListener('click',closePassport); passportBackdrop?.addEventListener('click',closePassport);

  surpriseBtn.addEventListener('click',()=>{let pool=places.filter(p=>!visited.has(p.id));if(!pool.length)pool=places;selectPlace(pool[Math.floor(Math.random()*pool.length)]);});
  unvisitedBtn.addEventListener('click',()=>{unvisitedOnly=!unvisitedOnly;unvisitedBtn.classList.toggle('active',unvisitedOnly);unvisitedBtn.textContent=unvisitedOnly?'Showing unvisited · clear':'Show unvisited';applyFilters();});

  renderList(places); applyFilters();
  const hashId=decodeURIComponent((location.hash||'').replace(/^#/,'')); if(hashId){const fromHash=places.find(p=>p.id===hashId);if(fromHash)setTimeout(()=>selectPlace(fromHash),120);}
})();

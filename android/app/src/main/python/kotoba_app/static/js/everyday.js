document.addEventListener('DOMContentLoaded', () => {
  const filterInput = document.getElementById('everyday-filter');
  const tabs = document.querySelectorAll('.cat-tab');
  const entries=JSON.parse(document.getElementById('everyday-catalog').textContent),list=document.getElementById('everyday-list'),more=document.getElementById('everyday-more'),renderCount=document.getElementById('everyday-render-count');
  let activeCat='all',limit=96,filtered=entries;
  function render(append=false){const start=append?list.querySelectorAll('.everyday-row').length:0;if(!append)list.replaceChildren();
    const counts=new Map();filtered.forEach(e=>counts.set(e[1],(counts.get(e[1])||0)+1));
    filtered.slice(start,limit).forEach(e=>{let block=[...list.children].find(b=>b.dataset.cat===e[1]);if(!block){block=document.createElement('section');block.className='category-block';block.dataset.cat=e[1];const h=document.createElement('h2');h.className='category-heading';h.textContent=e[1]+' ('+counts.get(e[1])+')';const table=document.createElement('div');table.className='everyday-table';block.append(h,table);list.append(block);}const row=document.createElement('button');row.type='button';row.className='everyday-row';row.dataset.idx=e[0];row.dataset.search=e[7];for(const[cls,text]of [['everyday-emoji',e[2]],['everyday-word',e[3]],['everyday-reading',e[4]],['everyday-romaji',e[5]],['everyday-meaning',e[6]]]){const span=document.createElement('span');span.className=cls;span.textContent=text;row.append(span);}block.lastElementChild.append(row);});
    const shown=list.querySelectorAll('.everyday-row').length;more.hidden=shown>=filtered.length;renderCount.textContent=filtered.length?'Showing '+shown+' of '+filtered.length+' matching words':'No words match this filter.';}
  function applyFilters(){const q=filterInput.value.trim();filtered=entries.filter(e=>(activeCat==='all'||e[1]===activeCat)&&(!q||KotobaSearchMatch.matches(e[7],q)));limit=96;render();}
  tabs.forEach(tab=>tab.addEventListener('click',()=>{tabs.forEach(t=>t.classList.remove('active'));tab.classList.add('active');activeCat=tab.dataset.cat;applyFilters();}));
  filterInput.addEventListener('input',applyFilters);more.addEventListener('click',()=>{limit+=96;render(true);});
  applyFilters();

  // ---------------- word detail modal ----------------
  const modal = document.getElementById('word-modal');
  const convoEl = document.getElementById('modal-convo');

  function setText(id, value) {
    document.getElementById(id).textContent = value || '';
  }

  function renderModal(entry) {
    setText('modal-emoji', entry.emoji);
    setText('modal-word', entry.word);
    setText('modal-reading', `${entry.reading}  ·  ${entry.romaji}`);
    setText('modal-meaning', entry.meaning);
    const rank = entry.frequency_rank ? ` · Common #${entry.frequency_rank}` : '';
    const diff = entry.difficulty ? ` · ${entry.difficulty[0].toUpperCase() + entry.difficulty.slice(1)}` : '';
    setText('modal-category', `${entry.category}${diff}${rank}`);
    setText('modal-usage', entry.usage_note);
    const speakBtn = document.getElementById('modal-speak');
    if (speakBtn) speakBtn.onclick = () => window.KotobaSpeech && KotobaSpeech.speakReading(entry.word,entry.reading);
    const favBtn = document.getElementById('modal-favorite');
    if (favBtn) {
      favBtn.onclick = async () => {
        if (!window.KotobaLearn) return;
        const r = await KotobaLearn.favorite({kind:'vocab', id:entry.word, front:entry.word, reading:entry.reading || entry.romaji || '', meaning:entry.meaning, url:'/everyday'});
        if (r) { favBtn.textContent = r.added ? '★ Saved' : '☆ Save'; KotobaLearn.toast(r.added ? 'Saved to Favorites' : 'Removed from Favorites'); }
      };
    }

    convoEl.innerHTML = '';
    (entry.conversation || []).forEach(line => {
      const wrap = document.createElement('div');
      wrap.className = 'convo-line convo-' + line.speaker.toLowerCase();

      const who = document.createElement('span');
      who.className = 'convo-speaker';
      who.textContent = line.speaker;
      wrap.appendChild(who);

      const body = document.createElement('div');
      body.className = 'convo-body';
      [
        ['convo-kanji', line.kanji],
        ['convo-hiragana', line.hiragana],
        ['convo-romaji', line.romaji],
        ['convo-english', line.english],
      ].forEach(([cls, text]) => {
        const p = document.createElement('p');
        p.className = cls;
        p.textContent = text;
        body.appendChild(p);
      });
      const listen = document.createElement('button'); listen.type='button'; listen.className='line-speak'; listen.textContent='🔊'; listen.setAttribute('aria-label','Listen'); listen.onclick=()=>window.KotobaSpeech&&KotobaSpeech.speakReading(line.kanji,line.hiragana); body.appendChild(listen);
      wrap.appendChild(body);
      convoEl.appendChild(wrap);
    });
  }

  function closeModal() {
    requestId++;
    if(window.KotobaSpeech)KotobaSpeech.stop();
    modal.hidden = true;
    document.body.style.overflow = '';
  }

  let requestId=0;
  async function openEntry(idx){const token=++requestId;modal.hidden=false;document.body.style.overflow='hidden';convoEl.innerHTML='<p class="convo-loading">Loading...</p>';try{const res=await fetch('/api/everyday/'+idx);if(!res.ok)throw Error('bad status');const entry=await res.json();if(token===requestId&&!modal.hidden)renderModal(entry);}catch(_){if(token===requestId&&!modal.hidden)convoEl.innerHTML='<p class="convo-loading">Could not load this word.</p>';}}
  list.addEventListener('click',e=>{const row=e.target.closest('.everyday-row');if(row)openEntry(row.dataset.idx);});
  // Exact global-search results open even outside the first displayed batch.
  const entry=new URLSearchParams(location.search).get('entry');if(entry!==null&&/^\d+$/.test(entry)&&entries.some(e=>String(e[0])===entry))openEntry(entry);

  document.getElementById('modal-close').addEventListener('click', closeModal);
  modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !modal.hidden) closeModal();
  });
});

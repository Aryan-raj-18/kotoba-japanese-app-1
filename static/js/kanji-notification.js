(function () {
  'use strict';
  var page=document.getElementById('kanji-notification-page');if(!page)return;
  var native=window.KotobaKanjiNotificationNative,rows=[],selected=new Set(),loadToken=0,pending='',state={enabled:false,allowed:false};
  function el(name){return document.getElementById('kanji-notification-'+name);}
  function status(text){el('status').textContent=text;}
  function pool(){return el('pool').value==='all'?rows:Array.from(selected).map(function(char){return rows.find(function(r){return r.kanji===char;});}).filter(Boolean);}
  function config(){return {level:el('level').value,selected:el('pool').value==='all'?[]:Array.from(selected),mode:el('mode').value,minutes:Number(el('minutes').value),meaning:el('meaning').checked,readings:el('readings').checked};}
  function preview(){
    var deck=pool(),card=deck.find(function(r){return r.kanji===state.current;})||deck[0];
    el('preview-char').textContent=card?card.kanji:'—';el('preview-meaning').textContent=card?(el('meaning').checked?card.meaning:'Recall the meaning'):'Choose a kanji';
    el('preview-readings').textContent=card&&el('readings').checked?[card.on?'On: '+card.on:'',card.kun?'Kun: '+card.kun:''].filter(Boolean).join(' · '):'';el('preview-level').textContent='JLPT '+el('level').value;
  }
  function choices(){
    var q=el('search').value.trim().toLowerCase(),list=el('choices');list.replaceChildren();
    rows.filter(function(r){return !q||[r.kanji,r.meaning,r.on,r.kun].join(' ').toLowerCase().includes(q);}).forEach(function(r){var label=document.createElement('label'),check=document.createElement('input'),text=document.createElement('span');label.className='kanji-notification-choice';check.type='checkbox';check.value=r.kanji;check.checked=selected.has(r.kanji);text.textContent=r.kanji+' · '+r.meaning;label.append(check,text);list.append(label);});
    if(!list.children.length){var empty=document.createElement('p');empty.textContent='No kanji found. Try another character or meaning.';list.append(empty);}
    list.scrollTop=0;selectionSummary();
  }
  function selectionSummary(){
    el('selected').textContent=selected.size+' selected'+(selected.size?' · '+Array.from(selected).slice(0,24).join(' ')+(selected.size>24?' …':''):'');
  }
  function controls(){
    el('selection').hidden=el('pool').value!=='selected';el('duration').hidden=el('mode').value==='hold';el('minutes').disabled=el('mode').value==='hold';
    el('minutes').min=el('mode').value==='rotate'?'15':'1';
    el('duration-hint').textContent=(el('mode').value==='rotate'?'15 minutes':'1 minute')+' to 24 hours. Android may delay changes while the phone sleeps or saves battery.';
    el('apply').disabled=!native||!!pending||!rows.length;el('stop').disabled=!native;el('next').disabled=!native||!state.enabled;el('system').hidden=!native;el('phone-settings').hidden=!native||typeof native.openPhoneSettings!=='function';selectionSummary();preview();
  }
  function readState(updateForm){
    if(!native)return;
    try{state=JSON.parse(native.getState());if(updateForm){el('level').value=state.level;selected=new Set(state.selected||[]);el('pool').value=selected.size?'selected':'all';el('mode').value=state.mode;el('minutes').value=state.minutes;el('meaning').checked=state.meaning;el('readings').checked=state.readings;}}catch(e){status('Could not read notification settings. Try reopening this section.');}
  }
  async function load(){
    var token=++loadToken;rows=[];choices();controls();status('Loading '+el('level').value+' kanji…');
    try{var response=await fetch('/api/kanji-notification/catalog?level='+encodeURIComponent(el('level').value));if(!response.ok)throw Error('catalog');var data=await response.json();if(token!==loadToken)return;rows=data.cards;var valid=new Set(rows.map(function(r){return r.kanji;}));selected=new Set(Array.from(selected).filter(function(x){return valid.has(x);}));choices();controls();status(native?(state.enabled?(state.allowed?'Your kanji notification is active.':'Notifications are blocked in Android settings.'):'Choose your cards, then tap Show my kanji.'):'Preview available here. Open the installed Kotoba Android app to show notifications.');}
    catch(e){if(token===loadToken){controls();status('Could not load these cards. Try selecting the level again.');}}
  }
  window.KotobaKanjiNotification={receive:function(id,next,error){if((id&&id!==pending)||(!id&&pending))return;pending='';state=next;controls();status(error||(next.enabled?'Your kanji notification is active.':'Kanji notification stopped.'));}};
  readState(true);
  var params=new URLSearchParams(location.search),level=params.get('level'),char=params.get('kanji');
  if(['N5','N4','N3','N2','N1'].includes(level)){el('level').value=level;if(char){selected=new Set([char]);el('pool').value='selected';}}
  el('level').addEventListener('change',function(){selected.clear();el('search').value='';load();});
  ['pool','mode','meaning','readings'].forEach(function(name){el(name).addEventListener('change',controls);});el('search').addEventListener('input',choices);
  el('choices').addEventListener('change',function(event){var check=event.target;if(check.type!=='checkbox')return;if(check.checked)selected.add(check.value);else selected.delete(check.value);selectionSummary();preview();});
  el('clear').addEventListener('click',function(){selected.clear();el('choices').querySelectorAll('input').forEach(function(check){check.checked=false;});selectionSummary();preview();});
  el('form').addEventListener('submit',function(event){event.preventDefault();if(!native||pending)return;var value=config();if(!pool().length){status('Select at least one kanji.');el('choices').focus();return;}if(value.mode==='hold')value.minutes=60;
    var minimum=value.mode==='rotate'?15:1;
    if(!Number.isInteger(value.minutes)||value.minutes<minimum||value.minutes>1440){status('Choose a whole number from '+minimum+' to 1440 minutes.');el('minutes').focus();return;}
    pending='kanji:'+Date.now();controls();status('Saving your card and checking notification permission…');try{native.apply(JSON.stringify(value),pending);}catch(e){pending='';controls();status('Could not show the card. Try again.');}
  });
  el('stop').addEventListener('click',function(){if(native){pending='';native.stop();}});el('next').addEventListener('click',function(){if(native)native.next();});el('system').addEventListener('click',function(){if(native)native.openSettings();});
  el('phone-settings').addEventListener('click',function(){if(native&&native.openPhoneSettings)native.openPhoneSettings();});
  document.addEventListener('visibilitychange',function(){if(!document.hidden){readState(false);controls();if(native)status(state.enabled?(state.allowed?'Your kanji notification is active.':'Notifications are blocked in Android settings.'):'Kanji notification stopped.');}});
  load();
})();

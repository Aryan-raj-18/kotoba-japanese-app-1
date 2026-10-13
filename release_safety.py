"""Validation, recoverable local state and atomic writes; no external services."""
import json, math, os, tempfile, threading
from pathlib import Path
from contextlib import contextmanager

_local = threading.local()
COUNTERS = {'xp','reviews','correct','lapses','streak','count','recovered','audio','speaking','lessons','mock','explore','right','total','score','quality'}
NUMBERS = {'interval','ease'}
TEXT = {'key','id','kind','front','answer','reading','meaning','sub','prompt','chosen','correct_answer','explanation','level','source_url','url','added','last_review','last_missed','next_review','title','label','date','created','at','approx_level','recommendation','chapter_id','chapter_title','mastery','city'}

def atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    journal = getattr(_local, 'journal', None)
    if journal is not None and path not in journal:
        journal[path] = path.read_bytes() if path.exists() else None
    fd, name = tempfile.mkstemp(prefix=path.name+'.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, allow_nan=False, indent=2)
            handle.flush(); os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)

@contextmanager
def transaction():
    journal = {}; _local.journal = journal
    try:
        yield
    except BaseException:
        _local.journal = None
        for path, content in reversed(list(journal.items())):
            if content is None: path.unlink(missing_ok=True)
            else:
                fd,name=tempfile.mkstemp(dir=str(path.parent),suffix='.rollback')
                with os.fdopen(fd,'wb') as handle:
                    handle.write(content);handle.flush();os.fsync(handle.fileno())
                os.replace(name,path)
        raise
    finally:
        _local.journal = None

def strict_state(state):
    if not isinstance(state,dict): raise ValueError('Learner state must be an object')
    def walk(value, key='', depth=0):
        if depth > 12: raise ValueError('Backup nesting is too deep')
        if key in COUNTERS:
            if key=='correct' and depth>=3 and type(value) is bool: return
            if type(value) is not int or not 0 <= value <= 10**10: raise ValueError('Invalid counter: '+key)
        elif key in TEXT:
            if value is not None and not isinstance(value,str) and not (key=='id' and type(value) is int):raise ValueError('Invalid text: '+key)
        elif key in NUMBERS:
            if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=10000: raise ValueError('Invalid number: '+key)
        if isinstance(value,dict):
            if len(value)>50000: raise ValueError('Backup collection is too large')
            for k,v in value.items():
                if not isinstance(k,str) or len(k)>2000: raise ValueError('Invalid backup key')
                walk(v,k,depth+1)
        elif isinstance(value,list):
            if len(value)>50000: raise ValueError('Backup list is too large')
            for v in value: walk(v,'',depth+1)
        elif isinstance(value,str):
            if len(value)>20000: raise ValueError('Backup text is too large')
        elif value is not None and type(value) not in (int,float,bool): raise ValueError('Unsupported backup value')
        elif type(value) is float and not math.isfinite(value): raise ValueError('Non-finite backup number')
    walk(state)
    for key in ['srs','mistakes','lists','daily','japan_visited']:
        if key in state and not isinstance(state[key],dict): raise ValueError(key+' must be an object')
    for key in ['history','mock_history']:
        if key in state and (not isinstance(state[key],list) or any(not isinstance(x,dict) for x in state[key])): raise ValueError(key+' must contain objects')
    for key in ['srs','mistakes','japan_visited']:
        if any(not isinstance(v,dict) for v in state.get(key,{}).values()): raise ValueError(key+' contains an invalid entry')
    for items in state.get('lists',{}).values():
        if not isinstance(items,list) or any(not isinstance(x,dict) for x in items): raise ValueError('Invalid favorites list')
    if state.get('placement') is not None and not isinstance(state['placement'],dict): raise ValueError('Invalid placement')
    if state.get('correct',0)>state.get('reviews',state.get('correct',0)): raise ValueError('Correct count exceeds reviews')
    return state

def normalise_state(state):
    """Repair malformed counters/collections without discarding valid progress."""
    def clean(value):
        if not isinstance(value,dict): return {}
        out=dict(value)
        for key in COUNTERS & out.keys():
            try:out[key]=max(0,min(10**10,int(out[key])))
            except (ValueError,TypeError,OverflowError):out[key]=0
        for key in NUMBERS & out.keys():
            try:
                n=float(out[key]);out[key]=n if math.isfinite(n) and 0<=n<=10000 else 0
            except (ValueError,TypeError,OverflowError):out[key]=0
        for key in TEXT & out.keys():
            if not isinstance(out[key],str):out[key]=str(out[key]) if key=='id' and type(out[key]) is int else ''
        return out
    state=clean(state)
    for key in ['srs','mistakes','japan_visited']:
        state[key]={k:clean(v) for k,v in state.get(key,{}).items() if isinstance(v,dict)}
    state['daily']=clean(state.get('daily',{}))
    state['lists']={k:[v for v in items if isinstance(v,dict)] for k,items in state.get('lists',{}).items() if isinstance(items,list)}
    for key in ['history','mock_history']:state[key]=[clean(v) for v in state.get(key,[]) if isinstance(v,dict)]
    if not isinstance(state.get('placement'),dict):state['placement']=None
    state['correct']=min(state.get('correct',0),state.get('reviews',0))
    return state

def validate_backup(payload, decks, chapters):
    from datetime import date
    if not isinstance(payload,dict) or payload.get('format')!='kotoba-backup-v1': raise ValueError('Choose a Kotoba backup file')
    if 'learner' in payload: strict_state(payload['learner'])
    if 'progress' in payload:
        if not isinstance(payload['progress'],dict): raise ValueError('Invalid progress')
        for key,items in payload['progress'].items():
            if key not in decks or not isinstance(items,list) or any(not isinstance(x,str) for x in items): raise ValueError('Invalid progress deck')
    if 'roadmap_completed' in payload:
        items=payload['roadmap_completed']
        if not isinstance(items,list) or any(not isinstance(x,str) for x in items): raise ValueError('Invalid roadmap progress')
    if payload.get('roadmap_start') is not None and payload['roadmap_start'] not in chapters: raise ValueError('Unknown roadmap starting point')
    if 'streak_dates' in payload:
        if not isinstance(payload['streak_dates'],list): raise ValueError('Invalid streak dates')
        for day in payload['streak_dates']:
            if not isinstance(day,str): raise ValueError('Invalid streak date')
            date.fromisoformat(day)
    return payload

def validate_api(endpoint, payload):
    if not isinstance(payload,dict): raise ValueError('Send a JSON object')
    for key in ['kind','sub','url','word','pattern','chapter_id','item_id_text','front','prompt','difficulty','action','name','list','source','target','key','deck','message','topic','level','place_id','answer','reading','meaning','chosen','correct_answer','explanation','source_url']:
        if key in payload and payload[key] is not None and (not isinstance(payload[key],str) or len(payload[key])>20000):raise ValueError('Invalid '+key)
    if 'id' in payload and (type(payload['id']) not in (str,int) or len(str(payload['id']))>2000):raise ValueError('Invalid id')
    if 'known' in payload and type(payload['known']) is not bool:raise ValueError('Known must be true or false')
    if 'chapter_id' in payload and not isinstance(payload['chapter_id'],str):raise ValueError('Invalid chapter id')
    if 'correct' in payload and type(payload['correct']) is not bool:raise ValueError('Correct must be true or false')
    for key,minimum,maximum in [('count',1,100),('amount',1,100),('quality',1,5),('score',0,200),('total',1,200)]:
        if key in payload and (type(payload[key]) is not int or not minimum<=payload[key]<=maximum):raise ValueError('Invalid '+key)
    if 'item' in payload:
        if not isinstance(payload['item'],dict):raise ValueError('Item must be an object')
        validate_api(endpoint,payload['item'])
    if endpoint=='api_jlpt_mock_save':
        if payload.get('level') not in {'N5','N4','N3','N2','N1'} or payload.get('score',0)>payload.get('total',1):raise ValueError('Invalid mock score')

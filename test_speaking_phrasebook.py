"""Regression checks for original Speaking & Shadowing scenarios."""
from collections import Counter
from app import app, SPEAKING_PHRASEBOOK, _speaking_items

assert len(SPEAKING_PHRASEBOOK) == 360, len(SPEAKING_PHRASEBOOK)
assert len({x['id'] for x in SPEAKING_PHRASEBOOK}) == 360
assert len({x['jp'] for x in SPEAKING_PHRASEBOOK}) == 360
categories={x['category'] for x in SPEAKING_PHRASEBOOK}
assert len(categories) == 24
assert Counter(x['level'] for x in SPEAKING_PHRASEBOOK) == {'easy':120,'medium':168,'hard':72}
for x in SPEAKING_PHRASEBOOK:
    assert x['id'].startswith('original-')
    assert x.get('jp') and x.get('reading') and x.get('romaji') and x.get('english')
    assert x.get('authorship') == 'original'
    assert 'source_page' not in x

for level in ('easy','medium','hard'):
    rows=_speaking_items(level,'phrasebook')
    assert rows and all(r['id'].startswith('phrase-original-') for r in rows)
    assert all(r['level']==level for r in rows)
    assert all(r['source'].startswith('Everyday scenarios · ') for r in rows)

client=app.test_client()
page=client.get('/speaking')
assert page.status_code==200
assert b'Choose a situation' in page.data
res=client.get('/api/speaking_items?source=phrasebook&level=easy&count=40')
assert res.status_code == 200
items=res.get_json()['items']
assert len(items)==40
assert all(x['id'].startswith('phrase-original-') for x in items)
assert all(x['level']=='easy' for x in items)

category='Learning Japanese'
filtered=_speaking_items('medium','phrasebook',category)
assert filtered and all(x['category']==category and x['level']=='medium' for x in filtered)
res=client.get('/api/speaking_items?source=phrasebook&level=medium&category=Learning%20Japanese&count=40')
assert res.status_code == 200
assert len(res.get_json()['items'])==len(filtered)
assert all(x['category']==category for x in res.get_json()['items'])

mixed=_speaking_items('all','all')
keys=[x['jp'].replace(' ','') for x in mixed]
assert len(keys)==len(set(keys)), 'mixed speaking pool has duplicate Japanese targets'
print('PASS: 360 original practice targets, category/level filters and deduplication')

"""Dependency-free checks for original speaking examples and romanization data."""
import json
from collections import Counter
from pathlib import Path
root = Path(__file__).resolve().parent
items = json.loads((root/'data/speaking_phrasebook.json').read_text(encoding='utf-8'))
assert len(items) == 360
assert len({item['id'] for item in items}) == 360
assert len({item['jp'] for item in items}) == 360
assert len({item['category'] for item in items}) == 24
assert Counter(item['level'] for item in items) == {'easy':120,'medium':168,'hard':72}
for entry in items:
    assert set(entry) == {'id','jp','reading','romaji','english','category','level','authorship'}
    assert entry['authorship']=='original' and entry['id'].startswith('original-')
    assert all(entry[k] for k in ['jp','reading','romaji','english','category'])
    assert 'source_page' not in entry
    assert all('ぁ' <= x <= 'ゖ' or x=='ー' for x in entry['reading']), entry
    assert all(ord(x)<128 for x in entry['romaji']), entry
by_category={}
for item in items:
    by_category.setdefault(item['category'], []).append(item)
for cat, group in by_category.items():
    assert len(group)==15,cat
    assert Counter(x['level'] for x in group)== {'easy':5,'medium':7,'hard':3},cat
android_data=root/'android/app/src/main/python/kotoba_app/data/speaking_phrasebook.json'
if android_data.is_file():
    assert android_data.read_bytes() == (root/'data/speaking_phrasebook.json').read_bytes(), 'Android data copy is stale'
print('PASS 360 original sentences in 24 situations, complete readings and Android sync')

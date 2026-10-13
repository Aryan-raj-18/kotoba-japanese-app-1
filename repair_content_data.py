#!/usr/bin/env python3
"""Repair identified import faults without replacing valid contextual senses.

Run before build_kanji_catalog.py. The audit records each changed source field.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / 'data'


def main():
    changes = []

    def load(name):
        return json.loads((DATA / name).read_text(encoding='utf-8'))

    def save(name, value):
        (DATA / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    # The importer omitted Hepburn ja/ju/jo from its syllable table.
    for name in ('frequency_words.json', 'grammar.json', 'picture_dict.json'):
        items = load(name)
        for w in items:
            old = w.get('reading', '')
            fixed = re.sub(r'j([あうお])', lambda m: {'あ': 'じゃ', 'う': 'じゅ', 'お': 'じょ'}[m[1]], old)
            if old == 'goーru':
                fixed = 'ごーる'
            if fixed != old:
                changes.append({'source': name, 'word': w.get('word', w.get('pattern')), 'field': 'reading', 'before': old, 'after': fixed})
                w['reading'] = fixed
        save(name, items)

    core = load('kanji_data.json')
    extra_path = DATA / 'kanji_vocab_extra.json'
    extras = load(extra_path.name) if extra_path.exists() else []
    # These are PDF page headers/mnemonic fragments, not dictionary entries.
    fragments = {('虫', '犬'), ('森', '木を見て'), ('達', 'する')}
    moves = []
    for parent in core:
        keep = []
        for raw in parent['vocab']:
            w = dict(raw)
            if (parent['kanji'], w['word']) in fragments:
                changes.append({'source': 'kanji_data.json', 'word': w['word'], 'action': 'remove import fragment', 'before': w})
                continue
            if w['word'] == 'じゅぎょう・授業':
                w.update(word='授業', reading='じゅぎょう', romaji='jugyō', meaning='lesson, class')
                changes.append({'source': 'kanji_data.json', 'word': '授業', 'action': 'restore word from existing frequency entry', 'before': raw, 'after': w})
            if w['word'] == '定員' and w['meaning'].strip() == 'tei':
                w.update(reading='ていいん', romaji='teiin', meaning='capacity; fixed number of people')
                changes.append({'source': 'kanji_data.json', 'word': '定員', 'action': 'restore truncated definition', 'before': raw, 'after': w})
            if parent['kanji'] not in w['word']:
                candidates = [k for k in core if k['kanji'] in w['word']]
                if candidates:
                    # Adjacent textbook columns were attached to the previous
                    # heading. Move only to a heading actually in the word.
                    target = min(candidates, key=lambda k: abs(k['id'] - parent['id']))
                    moves.append((target, w))
                    changes.append({'source': 'kanji_data.json', 'word': w['word'], 'action': 'correct parent', 'before': parent['kanji'], 'after': target['kanji']})
                    continue
                chars = [ch for ch in w['word'] if '\u4e00' <= ch <= '\u9fff']
                if chars:
                    extra = dict(w, kanji=chars[0])
                    if extra not in extras:
                        extras.append(extra)
                    changes.append({'source': 'kanji_data.json', 'word': w['word'], 'action': 'restore missing-character vocabulary in expanded catalog', 'before': parent['kanji'], 'after': chars[0]})
                    continue
            keep.append(w)
        parent['vocab'] = keep
    for target, w in moves:
        if not any((v['word'], v['reading'], v['meaning']) == (w['word'], w['reading'], w['meaning']) for v in target['vocab']):
            target['vocab'].append(w)
    save('kanji_data.json', core)
    save('kanji_vocab_extra.json', extras)

    report_path = ROOT / 'CONTENT_AUDIT.json'
    previous = json.loads(report_path.read_text(encoding='utf-8')).get('changes', []) if report_path.exists() else []
    history = previous + [c for c in changes if c not in previous]
    report = {'scope': 'Identified import faults and cross-section data consistency; not a certification of every translation.', 'changes': history, 'total_changes': len(history)}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Repaired', len(changes), 'source fields/associations')


if __name__ == '__main__':
    main()

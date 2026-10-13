"""Offline search over the app's actual learning content (Python 3.8)."""
import re
import hashlib
import unicodedata
from collections import defaultdict
from array import array
from functools import lru_cache
from bisect import bisect_left
from urllib.parse import quote


def normalize(text):
    """Fold width, kana, Latin accents and punctuation, preserving dakuten."""
    text = unicodedata.normalize('NFKC', str(text or '')).casefold()
    out = []
    for char in text:
        if '\u30a1' <= char <= '\u30f6':
            char = chr(ord(char) - 0x60)
        if 'LATIN' in unicodedata.name(char, ''):
            char = ''.join(c for c in unicodedata.normalize('NFD', char)
                           if not unicodedata.combining(c))
        if char in "'’":
            continue
        if unicodedata.category(char)[0] in ('P', 'S', 'Z', 'C'):
            char = ' '
        out.append(char)
    return ' '.join(''.join(out).split())


def compact(text):
    return normalize(text).replace(' ', '')


def text_matches(value, query):
    """English uses token boundaries; Japanese permits unspaced substrings."""
    value, query = normalize(value), normalize(query)
    if not query:
        return False
    if re.search('[a-z]', query):
        pattern = r'(?<![a-z0-9])' + re.escape(query) + r'(?![a-z0-9])'
        return bool(re.search(pattern, value))
    return query.replace(' ', '') in value.replace(' ', '')


PAST_VERBS = {
    'be': 'was/were', 'begin': 'began', 'bend': 'bent', 'drive': 'drove', 'throw': 'threw', 'blow': 'blew', 'buy': 'bought',
    'catch': 'caught', 'choose': 'chose', 'come': 'came', 'dig': 'dug',
    'do': 'did', 'drink': 'drank', 'eat': 'ate', 'fall': 'fell', 'feel': 'felt',
    'fish': 'fished', 'fly': 'flew', 'forget': 'forgot', 'get': 'got',
    'give': 'gave', 'go': 'went', 'have': 'had', 'hold': 'held', 'know': 'knew',
    'leave': 'left', 'lend': 'lent', 'make': 'made', 'meet': 'met',
    'put': 'put', 'read': 'read', 'ride': 'rode', 'run': 'ran', 'say': 'said',
    'see': 'saw', 'send': 'sent', 'shine': 'shone', 'sing': 'sang', 'sit': 'sat',
    'sleep': 'slept', 'speak': 'spoke', 'stand': 'stood', 'swim': 'swam',
    'take': 'took', 'teach': 'taught', 'tell': 'told', 'think': 'thought',
    'understand': 'understood', 'wear': 'wore', 'write': 'wrote', 'pay': 'paid',
}


def verb_form_meaning(meaning, form):
    labels = {'masu': 'Polite present / future', 'masu_neg': 'Polite negative',
              'past': 'Plain past', 'past_polite': 'Polite past', 'te': 'Te-form (connects phrases)',
              'nai': 'Plain negative', 'potential': 'Potential (ability)', 'volitional': 'Volitional (intention / suggestion)'}
    phrases = re.split(r',\s*(?=to )', meaning)
    glosses = []
    for phrase in phrases:
        base = re.sub(r'^to\s+', '', phrase.strip())
        head, sep, rest = base.partition(' ')
        if form in ('past', 'past_polite'):
            if head in PAST_VERBS:
                past = PAST_VERBS[head]
            elif head.endswith('e'):
                past = head + 'd'
            elif len(head) > 1 and head.endswith('y') and head[-2] not in 'aeiou':
                past = head[:-1] + 'ied'
            elif head in ('stop', 'wrap', 'log'):
                past = head + head[-1] + 'ed'
            else:
                past = head + 'ed'
            gloss = past + sep + rest
        elif form in ('masu_neg', 'nai'):
            gloss = ('not ' if head in ('be', 'exist') else 'do not ') + base
        elif form == 'potential':
            gloss = 'can ' + base
        elif form == 'volitional':
            gloss = "let's " + base
        else:
            gloss = base
        glosses.append(gloss)
    return '; '.join(glosses), labels[form]


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from strings(child)


def block_reading(blocks):
    """Read existing ruby data; never guess readings for unknown kanji."""
    if isinstance(blocks, str):
        return blocks
    if isinstance(blocks, dict):
        return blocks.get('reading') or blocks.get('text', '')
    if isinstance(blocks, list):
        return ''.join(block_reading(b) for b in blocks)
    return ''


TEXT_KEYS = {'word', 'jp', 'kanji', 'char', 'glyph', 'pattern', 'reading', 'kana',
             'hiragana', 'romaji', 'meaning', 'en', 'english', 'on_yomi', 'kun_yomi',
             'sentence', 'sentence_kanji', 'sentence_hiragana', 'sentence_romaji',
             'sentence_en', 'example_ja', 'example_en', 'example', 'example_reading',
             'correct', 'prompt', 'options', 'answer', 'explanation', 'q', 'q_en',
             'name', 'forms', 'note', 'origin', 'title', 'title_en', 'title_jp',
             'summary', 'setting', 'scene', 'description', 'tagline', 'famous', 'foods'}


class SearchIndex:
    def __init__(self):
        self.documents = []
        self.fields = []
        self.match_fields = []
        self.by_entry_id = {}
        self.by_word = defaultdict(list)
        self.exact = defaultdict(set)
        self.grams = {}
        self._seen = {}
        self.source_counts = defaultdict(int)
        self._suggest_keys = None
        self._suggest_entries = {}

    def _prepare_suggestions(self):
        # Built lazily so opening unrelated sections pays no autocomplete cost.
        entries = defaultdict(set)
        for idx, item in enumerate(self.documents):
            if item['kind'] == 'Sentence':
                continue
            for field in ('word', 'reading', 'romaji'):
                value = normalize(item.get(field))
                if value:
                    entries[value].add(idx)
            for sense in re.split(r'[;,/()]', normalize(item.get('meaning'))):
                sense = re.sub(r'^(?:to|a|an) ', '', sense.strip())
                if sense:
                    entries[sense].add(idx)
        self._suggest_entries = entries
        self._suggest_keys = sorted(entries)

    @lru_cache(maxsize=128)
    def suggested_ids(self, query):
        q = normalize(query)
        if not q or len(q) > 100:
            return ()
        if self._suggest_keys is None:
            self._prepare_suggestions()
        scores = {}
        pos = bisect_left(self._suggest_keys, q)
        while pos < len(self._suggest_keys):
            key = self._suggest_keys[pos]
            if not key.startswith(q):
                break
            for idx in self._suggest_entries[key]:
                item = self.documents[idx]
                score = (120 if key == q else 80)
                if any(normalize(item.get(field)).startswith(q) for field in ('word', 'reading', 'romaji')):
                    score += 12
                score += {'Word': 15, 'Kanji': 8, 'Kana': 5}.get(item['kind'], 0)
                scores[idx] = max(scores.get(idx, 0), score)
            pos += 1
        return tuple(sorted(scores, key=lambda i: (-scores[i], len(self.documents[i]['word']), i)))

    def suggest(self, query, limit=8):
        return [self.documents[i] for i in self.suggested_ids(query)[:limit]]

    def add(self, word, reading='', romaji='', meaning='', kind='Word', source='',
            href='', aliases=(), legacy=None, details=None):
        if not str(word or '').strip():
            return
        values = [word, reading, romaji, meaning] + list(strings(aliases))
        folded = {compact(v) for v in values} - {''}
        readable = {normalize(v) for v in values} - {''}
        if not folded:
            return
        key = (kind, word if kind == 'Kana' else compact(word), compact(reading), compact(meaning))
        if key in self._seen:
            idx = self._seen[key]
            folded -= self.fields[idx]
            self.fields[idx].update(folded)
            self.match_fields[idx].update(readable)
        else:
            idx = len(self.documents)
            self._seen[key] = idx
            item = dict(legacy or {})
            item.update(word=word, reading=reading or '', romaji=romaji or '',
                        meaning=meaning or '', kind=kind, source=source, source_href=href,
                        search_id=idx)
            entry_id = hashlib.sha256(repr(key).encode('utf-8')).hexdigest()[:20]
            item.update(entry_id=entry_id,
                        href=href if kind == 'Section' else '/search/entry/' + entry_id,
                        meaning_label='Translation' if kind == 'Sentence' else 'Meaning',
                        sources=[], examples=[])
            self.by_entry_id[entry_id] = item
            self.documents.append(item)
            self.by_word[word].append(item)
            self.fields.append(set(folded))
            self.match_fields.append(readable)
            self.source_counts[source.split(' · ')[0]] += 1
        item = self.documents[idx]
        ref = {'name': source, 'href': href}
        if href and ref not in item['sources']:
            item['sources'].append(ref)
        if details:
            for field, value in details.items():
                if field == 'examples':
                    for example in value:
                        if example not in item['examples']:
                            item['examples'].append(example)
                elif value:
                    item[field] = value
    def finish(self):
        # Compact integer postings keep the offline index affordable on phones.
        for idx, values in enumerate(self.fields):
            grams = set()
            for value in values:
                self.exact[value].add(idx)
                grams.update(value[i:i + 3] for i in range(len(value) - 2))
            for gram in grams:
                if gram not in self.grams:
                    self.grams[gram] = array('I')
                self.grams[gram].append(idx)
        self._seen.clear()
        return self

    def candidates(self, query):
        if len(query) < 3:
            return range(len(self.documents))
        buckets = [self.grams.get(query[i:i + 3], set())
                   for i in range(len(query) - 2)]
        smallest = min(buckets, key=len)
        return smallest  # Verify the complete substring against the original field below.

    def _rank(self, query):
        q = compact(query)
        if not q:
            return {}
        ranked = {}
        for idx in self.candidates(q):
            values = self.match_fields[idx]
            if not any(text_matches(value, query) for value in values):
                continue
            item = self.documents[idx]
            primary = compact(item['word'])
            # A full dictionary sense such as "to stand" is a closer English
            # answer than a compound like "vegetable stand" or romaji "go".
            senses = re.split(r'[;,/()]', normalize(item['meaning']))
            exact_sense = any(normalize(query) == re.sub(r'^(?:to|a|an) ', '', s.strip()) for s in senses)
            if q == primary:
                score = 140
            elif exact_sense and item['kind'] in ('Word', 'Kanji', 'Verb form'):
                score = 130
            elif idx in self.exact.get(q, ()):
                score = 115
            elif text_matches(item['meaning'], query):
                score = 85
            else:
                score = 60
            score += {'Word': 8, 'Kanji': 4, 'Verb form': 3, 'Place': 2, 'Section': 2}.get(item['kind'], 0)
            ranked[idx] = score
        # All entered words must be present. Never turn an unmatched sentence
        # into an unrelated result just because it contains a common word.
        tokens = normalize(query).split()
        if 1 < len(tokens) <= 16 and all(len(t) >= 2 for t in tokens):
            possible = [set(self.candidates(t)) for t in tokens]
            for idx in set.intersection(*possible):
                if idx not in ranked and any(all(text_matches(v, t) for t in tokens) for v in self.match_fields[idx]):
                    ranked[idx] = 35
        return ranked

    @lru_cache(maxsize=128)
    def ranked_ids(self, query):
        ranked = self._rank(query)
        # Keep the original query; an explicit spoken command is a fallback.
        command = re.sub(r'^(?:search(?: for)?|find|look up|show me|translate|'
                         r'what is the meaning of|what is the japanese for)\s+',
                         '', query.strip(), flags=re.I)
        command = re.sub(r'(?:を検索(?:して)?|を探して)[。！!？?]*$', '', command)
        if command != query.strip():
            for idx, score in self._rank(command).items():
                ranked[idx] = max(ranked.get(idx, 0), score - 25)
        return tuple(sorted(ranked, key=lambda i: (-ranked[i], len(self.documents[i]['word']), i)))

    def search(self, query, limit=60, offset=0):
        return [self.documents[i] for i in self.ranked_ids(query)[offset:offset + limit]]


def build_index(data):
    index = SearchIndex()
    everyday = {w['word']: w['idx'] for w in data['EVERYDAY_WORDS']}

    def vocab_href(w):
        if w.get('kanji_id'):
            return '/kanji/' + str(w['kanji_id'])
        if w.get('roadmap_chapter'):
            return '/roadmap/' + quote(w['roadmap_chapter'])
        if w.get('word') in everyday:
            return '/everyday?entry=' + str(everyday[w['word']])
        return '/everyday'

    def record(w, href, source, kind='Word'):
        word = w.get('word') or w.get('jp') or w.get('kanji') or w.get('char') or w.get('pattern')
        # Examples are separate Sentence records. Matching an example must not
        # present its parent word as though it translated the query.
        aliases = []  # Parent kanji readings are not readings of this word.
        reading = w.get('reading') or w.get('hiragana') or w.get('kana', '')
        if kind == 'Word' and word in data['KANJI_ID_BY_CHAR'] and (not reading or reading == word):
            return  # A character gloss is a Kanji record, not a dictionary word.
        meaning = w.get('meaning') or w.get('en') or w.get('english', '')
        opposite_note = ''
        if 'opposite of' in meaning:
            opposite_note = meaning
            meaning = re.sub(r'\s*\([^)]*opposite of[^)]*\)', '', meaning).strip()
        examples = []
        jp = w.get('example_ja') or w.get('source_example_ja') or w.get('sentence_kanji')
        en = w.get('example_en') or w.get('source_example_en') or w.get('sentence_en')
        if jp and en:
            examples.append({'word': jp, 'reading': w.get('sentence_hiragana', ''), 'meaning': en})
        index.add(word, w.get('reading') or w.get('hiragana') or w.get('kana', ''),
                  w.get('romaji', ''), meaning,
                  kind, source, href, aliases, w if kind == 'Word' else None,
                  {'examples': examples, 'note': w.get('note') or opposite_note})

    def sentence(w, href, source):
        index.add(w.get('sentence_kanji') or w.get('kanji') or w.get('jp') or w.get('sentence') or w.get('correct'),
                  w.get('sentence_hiragana') or w.get('hiragana') or w.get('reading') or block_reading(w.get('blocks')),
                  w.get('sentence_romaji') or w.get('romaji', ''),
                  w.get('sentence_en') or w.get('english') or w.get('en', ''),
                  'Sentence', source, href)

    for w in data['VOCAB_POOL']:
        record(w, vocab_href(w), 'Vocabulary')
    for w in data['EVERYDAY_WORDS']:
        href = '/everyday?entry=' + str(w['idx'])
        record(w, href, 'Everyday Life')
        sentence(w, href, 'Everyday Life')
        for line in w.get('conversation', []):
            sentence(line, href, 'Everyday Life')
    # Original records retain alternate meanings/examples lost by deck deduplication.
    for name in ('COMMON_WORDS', 'PICTURE_DICT_WORDS', 'EVERYDAY_EXTRA', 'FREQUENCY_WORDS'):
        for w in data[name]:
            href = vocab_href(w)
            record(w, href, 'Vocabulary')
            sentence({'jp': w.get('example_ja'), 'en': w.get('example_en')}, href, 'Vocabulary example')
    for k in data['KANJI_CATALOG']:
        href = '/kanji/' + str(k['id'])
        index.add(k['kanji'], data['study_kanji_reading'](k), '', k.get('meaning', ''),
                  'Kanji', 'Kanji', href, [k.get('on_yomi', ''), k.get('kun_yomi', '')], {'kanji_id': k['id']})
        for w in k.get('vocab', []):
            record(w, href, 'Kanji vocabulary')
    for k in data['JLPT_KANJI']:
        index.add(k['kanji'], data['study_kanji_reading'](k), '', k.get('meaning', ''), 'Kanji',
                  'JLPT ' + k['level'], '/kanji/' + str(data['KANJI_ID_BY_CHAR'][k['kanji']]), [k.get('on_yomi', ''), k.get('kun_yomi', '')])
    for w in data['PRACTICE_SENTENCES']:
        sentence(w, '/kanji/' + str(w['kanji_id']), 'Kanji example')
    for name, href in (('HIRAGANA_DATA', '/hiragana'), ('KATAKANA_DATA', '/katakana')):
        for w in data[name]:
            record(w, href, href[1:].capitalize(), 'Kana')
    for r in data['RADICALS']:
        index.add(r['glyph'], r['name'], r['romaji'], r['meaning'], 'Radical', 'Radicals',
                  '/radicals/' + r['id'], [r.get('forms', '')], {'radical_id': r['id']})
    for v in data['VERBS_DATA']:
        href = '/verbs?entry=' + str(v['idx'])
        record(v, href, 'Verbs')
        for form, w in v.get('forms', {}).items():
            gloss, label = verb_form_meaning(v['meaning'], form)
            index.add(w['kanji'], w.get('kana', ''), '', gloss,
                      'Verb form', 'Verbs · ' + v['word'], href, (), details={
                          'form_label': label, 'base_word': v['word'], 'base_meaning': v['meaning']})
    for g in data['GRAMMAR_DATA']:
        href = '/grammar/' + g['id']
        record(g, href, 'Grammar', 'Grammar')
        sentence({'jp': g.get('example_ja'), 'en': g.get('example_en')}, href, 'Grammar')
        for s in g.get('source_examples', []):
            sentence(s, href, 'Grammar')
    for name, section, base, lines in (('STORIES_DATA', 'Story', '/stories/', 'sentences'),
                                       ('CONVERSATIONS_DATA', 'Conversation', '/conversations/', 'lines')):
        for story in data[name]:
            href = base + story['id']
            source = section + ' · ' + story['title_en']
            index.add(story['title_jp'], '', '', story.get('summary') or story.get('setting'),
                      section, source, href, [story['title_en']], details={'meaning_label': 'Summary'})
            for s in story.get(lines, []) + story.get('phrases', []):
                sentence(s, href, source)
            for w in story.get('vocab', []):
                record(w, href, source)
            for q in story.get('questions', []):
                index.add(q.get('q'), '', '', q.get('q_en', ''), 'Question', source, href,
                          details={'meaning_label': 'Translation', 'note': q.get('explanation', '')})
    for section in data['ROADMAP']:
        for ch in section['chapters']:
            if ch.get('kind') != 'lesson':
                continue
            href = '/roadmap/' + ch['id']
            source = 'Roadmap · ' + ch['title']
            index.add(ch['title'], '', '', section['title'], 'Lesson', source, href)
            vocab = {w.get('jp'): w for w in ch.get('vocab', [])}
            for w in vocab.values():
                record(w, href, source)
            for s in ch.get('sentences', []):
                fill = vocab.get(s.get('blank'), {})
                sentence({'jp': s.get('jp', '').replace('___', s.get('blank', '')),
                          'reading': s.get('reading', '').replace('___', fill.get('reading') or s.get('blank', '')),
                          'romaji': s.get('romaji', '').replace('___', fill.get('romaji', '')),
                          'en': s.get('english', '')}, href, source)
            for point in ch.get('guide', {}).get('points', []):
                record(point, href, source, 'Grammar')
    japan = data['JAPAN_EXPLORER_DATA']
    for p in japan['places']:
        href = '/japan#' + p['id']
        source = 'Japan Explorer · ' + p['city_en']
        index.add(p['city_jp'], p['reading'], p['city_en'], p['prefecture_en'] + ' · ' + p['tagline'],
                  'Place', source, href, [p['prefecture_jp'], p['region'], p['famous'], p['foods'], p['description']],
                  {'japan_place': p['id']})
        for words in p.get('level_words', {}).values():
            for w in words:
                record(w, href, source)
        for s in p.get('phrases', {}).values():
            sentence(s, href, source)
        for s in p.get('situations', {}).values():
            sentence(s, href, source)
            index.add(s['title'], '', '', s['scene'], 'Situation', source, href, [s['prompt']], details={'meaning_label': 'Situation'})
    for w in japan.get('food_words', []):
        record(w, '/japan#' + w['place_id'], 'Japan Explorer · Local food')
    for words in japan.get('common_words', {}).values():
        for w in words:
            record(w, '/japan', 'Japan Explorer')
    for w in japan.get('train_vocab', []):
        record(w, '/japan', 'Japan Explorer')
    for region, d in japan.get('dialects', {}).items():
        href = '/japan#' + next(p['id'] for p in japan['places'] if p['region'] == region)
        record(d, href, 'Dialect · ' + region)
        sentence({'jp': d.get('example'), 'reading': d.get('example_reading'), 'en': d.get('example_en')}, href, 'Dialect · ' + region)
    for route in japan.get('train_routes', []):
        index.add(route['jp'], '', route['name'], route['description'], 'Journey', 'Japan Explorer', '/japan')
    for season in japan.get('seasons', {}).values():
        index.add(season['jp'], '', season['label'], season['tagline'], 'Season', 'Japan Explorer', '/japan')
    for level, questions in data['JLPT_EXAM_QUESTIONS'].items():
        for q in questions:
            href = '/jlpt/' + level + '/exam-practice'
            index.add(q['prompt'], '', '', q.get('explanation', ''), 'Exam example', 'JLPT ' + level + ' Exam',
                      href, (), details={'meaning_label': 'Answer explanation', 'note': 'Correct answer: ' + str(q.get('answer_label') or q.get('answer', ''))})
            if q.get('explanation'):
                index.add(q['explanation'], block_reading(q.get('explanation_blocks')), '', '',
                          'Sentence', 'JLPT ' + level + ' Exam', href)
    for title, href, aliases in [
        ('Daily Review', '/review', ['smart review', 'SRS', 'daily study']),
        ('Review Cards', '/flashcards', ['flashcards', 'vocabulary cards']),
        ('Japan Explorer', '/japan', ['Japan map', 'passport', 'train routes']),
        ('Roadmap', '/roadmap', ['chapters', 'lessons', 'learning path']),
        ('Grammar', '/grammar', ['grammar patterns']), ('Stories', '/stories', ['reading']),
        ('Conversations', '/conversations', ['dialogues']), ('Everyday Life', '/everyday', ['vocabulary']),
        ('Kanji', '/kanji', ['kanji words']), ('Verbs', '/verbs', ['conjugations']),
        ('Writing Practice', '/write', ['handwriting']), ('Speaking Practice', '/speaking', ['pronunciation']),
        ('My Lists', '/favorites', ['favorites', 'saved words']), ('Mistake Notebook', '/mistakes', ['mistakes']),
        ('JLPT Exams', '/jlpt', ['exam practice']), ('Progress', '/dashboard', ['dashboard', 'streak']),
        ('Games', '/games', ['learning games']), ('Hiragana', '/hiragana', ['hiragana chart']),
        ('Katakana', '/katakana', ['katakana chart']), ('Radicals', '/radicals', ['kanji radicals'])]:
        index.add(title, '', '', 'Open ' + title, 'Section', 'Kotoba', href, aliases)
    return index.finish()


# Build-time cache contains public learning content only, never learner state.
def _data_fingerprint(root):
    from pathlib import Path
    digest = hashlib.sha256()
    runtime = {'streak.json','feedback.json','users.json','user_streaks.json','progress.json','user_progress.json','roadmap_progress.json','user_roadmap_progress.json','roadmap_start.json','user_roadmap_start.json','learner_state.json','user_learner_state.json','device_learner.json'}
    for path in sorted((Path(root)/'data').glob('*.json')):
        if path.name not in runtime and not path.name.startswith(('search_cache','before_restore_')):
            digest.update(path.name.encode()); digest.update(path.read_bytes())
    return digest.hexdigest()

def _content_fingerprint(root):
    from pathlib import Path
    root=Path(root); digest=hashlib.sha256()
    files=[root/'app.py',root/'search_engine.py',root/'everyday_nl.py',root/'roadmap_extra.py']
    runtime={'streak.json','feedback.json','users.json','user_streaks.json','progress.json','user_progress.json','roadmap_progress.json','user_roadmap_progress.json','roadmap_start.json','user_roadmap_start.json','learner_state.json','user_learner_state.json','device_learner.json'}
    files+=sorted(p for p in (root/'data').glob('*.json') if p.name not in runtime and not p.name.startswith(('search_cache','before_restore_')))
    for path in files:
        raw=path.read_bytes()
        if path.name=='app.py':raw=raw.split(b'\n_server_lock =')[0].rstrip()+b'\n'
        digest.update(path.name.encode());digest.update(raw)
    return digest.hexdigest()

def write_cache(index, root, asset_build=''):
    import gzip,json
    from pathlib import Path
    index._prepare_suggestions()
    payload={'cache_version':2,'asset_build':asset_build,'data_fingerprint':_data_fingerprint(root),'fingerprint':_content_fingerprint(root),'documents':index.documents,'fields':[sorted(x) for x in index.fields],'match_fields':[sorted(x) for x in index.match_fields],'source_counts':dict(index.source_counts),'exact':{k:sorted(v) for k,v in index.exact.items()},'grams':{k:list(v) for k,v in index.grams.items()},'suggest_entries':{k:sorted(v) for k,v in index._suggest_entries.items()}}
    (Path(root)/'data'/'search_cache.json.gz').write_bytes(gzip.compress(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode(),compresslevel=6,mtime=0))

def load_or_build(data,root):
    import gzip,json
    from pathlib import Path
    try:
        payload=json.loads(gzip.decompress((Path(root)/'data'/'search_cache.json.gz').read_bytes()))
        if payload['cache_version']!=2 or payload['asset_build']!=data.get('ASSET_BUILD',''):
            raise ValueError('Stale cache format/build')
        modules = ['app.py','search_engine.py','everyday_nl.py','roadmap_extra.py']
        if all(not (Path(root)/name).exists() and (Path(root)/(name+'c')).exists() for name in modules):
            # Chaquopy ships compiled modules. Validate public data and build
            # when source files are unavailable on the installed phone.
            if payload['data_fingerprint']!=_data_fingerprint(root):raise ValueError('Stale compiled content cache')
        elif payload['fingerprint']!=_content_fingerprint(root):raise ValueError('Stale content cache')
        index=SearchIndex();index.documents=payload['documents'];index.fields=[set(x) for x in payload['fields']];index.match_fields=[set(x) for x in payload['match_fields']]
        for item in index.documents:index.by_entry_id[item['entry_id']]=item;index.by_word[item['word']].append(item)
        index.source_counts.update(payload['source_counts']);index.exact.update({k:set(v) for k,v in payload['exact'].items()});index.grams={k:array('I',v) for k,v in payload['grams'].items()}
        index._suggest_entries=payload['suggest_entries'];index._suggest_keys=sorted(index._suggest_entries)
        return index
    except (OSError,ValueError,KeyError,TypeError):return build_index(data)

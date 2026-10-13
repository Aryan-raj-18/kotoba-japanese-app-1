#!/usr/bin/env python3
"""Search coverage and behavior regressions; python test_search.py [--android]."""
import sys
import os,tempfile
os.environ["KOTOBA_DATA_DIR"]=tempfile.mkdtemp(prefix="kotoba-search-")
import re
import unittest
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

if '--android' in sys.argv:
    sys.argv.remove('--android')
    sys.path.insert(0, os.environ.get('KOTOBA_TEST_PACKAGE', str(Path(__file__).parent / 'android/app/src/main/python')))
    import kotoba_app.app as K
else:
    import app as K


class SearchTests(unittest.TestCase):
    def test_cached_suggestions_are_loaded_before_first_keystroke(self):
        self.assertIsNotNone(self.index._suggest_keys)
        self.assertTrue(self.index._suggest_keys)

    def test_partial_romaji_suggests_sora_with_its_own_meaning(self):
        rows = self.client.get('/api/search/suggest?q=sor').get_json()
        sky = next(r for r in rows if r['word'] == '空' and r['reading'] == 'そら')
        self.assertIn('sky', sky['meaning'].lower())
        self.assertEqual(self.client.get(sky['href']).status_code, 200)
        self.assertIn(sky['meaning'], self.client.get(sky['href']).get_data(as_text=True))
        self.assertNotIn('学校', [r['word'] for r in rows])

    def test_suggestions_keep_exact_words_ahead_of_prefixes(self):
        rows = self.index.suggest('sora', 12)
        self.assertTrue(rows)
        self.assertTrue(any(r['word'] == '空' for r in rows[:3]))
        self.assertTrue(self.index.suggest('wat'))
        self.assertTrue(self.index.suggest('ソラ'))
        self.assertEqual([r['entry_id'] for r in self.index.suggest('ＳＯＲ')],
                         [r['entry_id'] for r in self.index.suggest('sor')])

    def test_suggestions_are_bounded_and_do_not_invent_words(self):
        for q in ['', '。！？', 'zqxv987', 'a' * 101]:
            self.assertEqual(self.client.get('/api/search/suggest', query_string={'q': q}).get_json(), [])
        for limit, maximum in [('1', 1), ('9999', 12), ('bad', 8), ('-1', 1)]:
            rows = self.client.get('/api/search/suggest', query_string={'q': 's', 'limit': limit}).get_json()
            self.assertLessEqual(len(rows), maximum)
            for row in rows:
                original = self.index.by_entry_id[row['entry_id']]
                self.assertEqual(row['meaning'], original['meaning'])

    def test_submitted_partial_query_shows_clickable_suggestions(self):
        html = self.client.get('/search?q=sor').get_data(as_text=True)
        self.assertIn('Words starting with', html)
        self.assertIn('空', html)
        self.assertIn('sora', html)
        self.assertRegex(html, r'/static/js/search-suggestions\.js\?v=\d+')

    def test_prefixes_do_not_weaken_full_sentence_or_word_matching(self):
        self.assertEqual(self.index.search('sor'), [])
        self.assertNotIn('分かる', [r['word'] for r in self.index.search('stand')])
        self.assertFalse(self.index.suggest('where is the zqxv station'))

    def setUp(self):
        self.index = K.SEARCH_INDEX
        self.client = K.app.test_client()

    def assert_covered(self, text):
        key = K._search.compact(text)
        # A dictionary gloss can omit a parenthetical opposite note, while a
        # sentence containing that same note retains its full translation.
        if key and not self.index.exact.get(key) and isinstance(text, str) and 'opposite of' in text:
            text = re.sub(r'\s*\([^)]*opposite of[^)]*\)', '', text).strip()
            key = K._search.compact(text)
        if key:
            self.assertTrue(self.index.exact.get(key), 'Missing searchable field: ' + str(text))

    def test_device_study_selection_does_not_invalidate_content_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data').mkdir()
            for name in ('app.py', 'search_engine.py', 'everyday_nl.py', 'roadmap_extra.py'):
                (root / name).write_text('public content')
            (root / 'data' / 'common_words.json').write_text('[]')
            before = K._search._content_fingerprint(root)
            (root / 'data' / 'device_learner.json').write_text('{"legacy_id":1}')
            self.assertEqual(K._search._content_fingerprint(root), before)
            (root / 'data' / 'device_learner.json').write_text('{"legacy_id":null}')
            self.assertEqual(K._search._content_fingerprint(root), before)
            (root / 'data' / 'common_words.json').write_text('[{"word":"water"}]')
            self.assertNotEqual(K._search._content_fingerprint(root), before)

    def test_every_indexed_field_is_retrievable(self):
        # Audit every original display field and alias, not a hand-picked sample.
        # Exact postings + candidate membership prove the search can reach it.
        counts = Counter()
        for idx, doc in enumerate(self.index.documents):
            counts[doc['kind']] += 1
            for key in self.index.fields[idx]:
                self.assertIn(idx, self.index.exact[key])
                if len(key) >= 3:
                    self.assertIn(idx, self.index.candidates(key))
            for field in ('word', 'reading', 'romaji', 'meaning'):
                self.assert_covered(doc[field])
        print('\nSearch entries:', len(self.index.documents), dict(counts))
        print('Searchable normalized fields:', len(self.index.exact))

    def test_source_words_are_not_dropped(self):
        sources = ['VOCAB_POOL', 'EVERYDAY_WORDS', 'COMMON_WORDS', 'PICTURE_DICT_WORDS',
                   'FREQUENCY_WORDS', 'EVERYDAY_EXTRA', 'VERBS_DATA']
        for source in sources:
            for word in getattr(K, source):
                for field in ('word', 'reading', 'romaji', 'meaning'):
                    self.assert_covered(word.get(field))
        for source in (K.KANJI_CATALOG, K.JLPT_KANJI):
            for kanji in source:
                for field in ('kanji', 'on_yomi', 'kun_yomi', 'meaning'):
                    self.assert_covered(kanji.get(field))
        for section in K.ROADMAP:
            for ch in section['chapters']:
                if ch.get('kind') == 'lesson':
                    for word in ch.get('vocab', []):
                        for field in ('jp', 'reading', 'romaji', 'meaning'):
                            self.assert_covered(word.get(field))
        for source in (K.STORIES_DATA, K.CONVERSATIONS_DATA):
            for story in source:
                for word in story.get('vocab', []):
                    for field in ('word', 'reading', 'romaji', 'meaning'):
                        self.assert_covered(word.get(field))

    def test_source_sentences_are_not_dropped(self):
        for w in K.EVERYDAY_WORDS + K.PRACTICE_SENTENCES:
            for field in ('sentence_kanji', 'sentence_hiragana', 'sentence_romaji', 'sentence_en'):
                self.assert_covered(w.get(field))
            for line in w.get('conversation', []):
                for field in ('kanji', 'hiragana', 'romaji', 'english'):
                    self.assert_covered(line.get(field))
        for source, key in ((K.STORIES_DATA, 'sentences'), (K.CONVERSATIONS_DATA, 'lines')):
            for story in source:
                for line in story.get(key, []) + story.get('phrases', []):
                    for field in ('kanji', 'jp', 'hiragana', 'romaji', 'english', 'en'):
                        self.assert_covered(line.get(field))
        for word in K.FREQUENCY_WORDS + K.GRAMMAR_DATA:
            for field in ('example_ja', 'example_en'):
                self.assert_covered(word.get(field))
            for example in word.get('source_examples', []):
                self.assert_covered(example.get('sentence'))
        for place in K.JAPAN_PLACES:
            for words in place['level_words'].values():
                for word in words:
                    for field in ('jp', 'reading', 'en'):
                        self.assert_covered(word.get(field))
            for line in list(place['phrases'].values()) + list(place['situations'].values()):
                for field in ('jp', 'correct', 'reading', 'en'):
                    self.assert_covered(line.get(field))
        for section in K.ROADMAP:
            for ch in section['chapters']:
                if ch.get('kind') == 'lesson':
                    vocab = {w.get('jp'): w for w in ch.get('vocab', [])}
                    for line in ch.get('sentences', []):
                        w = vocab.get(line.get('blank'), {})
                        self.assert_covered(line.get('jp', '').replace('___', line.get('blank', '')))
                        self.assert_covered(line.get('reading', '').replace('___', w.get('reading') or line.get('blank', '')))
                        self.assert_covered(line.get('english'))
        for questions in K.JLPT_EXAM_QUESTIONS.values():
            for q in questions:
                self.assert_covered(q['prompt'])
                self.assert_covered(q.get('explanation'))

    def test_normalization_and_ranking(self):
        cases = [('water.', '水'), ('ＷＡＴＥＲ！', '水'), ('ゴハン', 'ご飯'),
                 ('ご は ん。', 'ご飯'), ('みす\u3099', '水'), ('ｺﾞﾊﾝ', 'ご飯'),
                 ('WHERE IS THE STATION?', 'すみません。駅はどこですか。'),
                 ('すみません 駅はどこですか', 'すみません。駅はどこですか。'),
                 ('図書館は静かです', '図書館は静かです。'),
                 ('行きました。', '行きました'), ('東京', '東京'), ('tōkyō', '東京'),
                 ('Search for water', '水'), ('水を検索して', '水')]
        for query, expected in cases:
            with self.subTest(query=query):
                results = K.search_words(query)
                self.assertIn(expected, [r['word'] for r in results[:8]])
        self.assertNotEqual(K._search.compact('か'), K._search.compact('が'))
        self.assertEqual(K.search_words('notawordzqxv987'), [])
        self.assertEqual(K.search_words('。！？'), [])
        self.assertEqual(K.search_words(''), [])
        self.assertTrue(K.search_words('water drink'))

    def test_api_and_pagination(self):
        response = self.client.get('/api/search', query_string={'q': 'water.', 'limit': 10})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 10)
        self.assertGreater(int(response.headers['X-Total-Count']), 10)
        next_page = self.client.get('/api/search', query_string={'q': 'water.', 'offset': 10, 'limit': 10}).get_json()
        self.assertFalse({x['search_id'] for x in response.get_json()} & {x['search_id'] for x in next_page})
        for page in ('2', '-1', 'bad', '1000000'):
            self.assertEqual(self.client.get('/search', query_string={'q': 'water.', 'page': page}).status_code, 200)
        html = self.client.get('/search', query_string={'q': '<script>alert(1)</script>'}).get_data(as_text=True)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_every_result_has_an_existing_destination(self):
        adapter = K.app.url_map.bind('localhost')
        paths = {urlsplit(doc['href']).path for doc in self.index.documents}
        paths.update(urlsplit(ref['href']).path for doc in self.index.documents for ref in doc['sources'])
        for path in paths:
            self.assertTrue(path.startswith('/'))
            adapter.match(path, method='GET')
        for doc in self.index.documents:
            if doc['kind'] != 'Section':
                self.assertIs(self.index.by_entry_id[doc['entry_id']], doc)
            for ref in doc['sources']:
                path = ref['href']
                if path.startswith('/kanji/'):
                    self.assertIn(int(path.rsplit('/', 1)[1]), {k['id'] for k in K.KANJI_CATALOG})
                elif '?entry=' in path:
                    idx = int(path.rsplit('=', 1)[1])
                    pool = K.VERBS_DATA if path.startswith('/verbs') else K.EVERYDAY_WORDS
                    self.assertTrue(0 <= idx < len(pool))
        for query in ['where is the station', '図書館は静かです', '行きました', '札幌へ行きたいです']:
            first = K.search_words(query)[0]
            self.assertEqual(self.client.get(first['href']).status_code, 200)

    def test_stand_does_not_match_understand_or_standard(self):
        results = self.index.search('stand', 10000)
        self.assertIn('立つ', [d['word'] for d in results[:5]])
        words = [d['word'] for d in results if d['kind'] == 'Word']
        for wrong in ['分かる', '理解', '基本的', '納得(する)']:
            self.assertNotIn(wrong, words)
        self.assertNotIn('dog', [d['meaning'].lower() for d in results])

    def test_examples_do_not_impersonate_word_definitions(self):
        for q in ['Where are you from?', '今日は仕事に行きました。', '小さい猫がいました。']:
            for doc in self.index.search(q):
                self.assertNotEqual(doc['kind'], 'Word', (q, doc))
        # Opposite notes are context, not the word's own definition.
        down = [d['word'] for d in self.index.search('down', 10000) if d['kind'] == 'Word']
        self.assertNotIn('上', down)

    def test_words_use_their_own_readings(self):
        results = self.index.search('そら', 10000)
        self.assertNotIn('学校', [d['word'] for d in results if d['kind'] == 'Word'])
        airport = next(d for d in self.index.search('学校') if d['word'] == '学校' and d['kind'] == 'Word')
        self.assertEqual(airport['reading'], 'がっこう')
        html = self.client.get(airport['href']).get_data(as_text=True)
        self.assertIn('data-reading="がっこう"', html)

    def test_word_details_preserve_the_clicked_word_and_meaning(self):
        for q, word in [('stand', '立つ'), ('dog', '犬'), ('猫', '猫'), ('水', '水')]:
            doc = next(d for d in self.index.search(q, 10000) if d['word'] == word and d['kind'] == 'Word')
            html = self.client.get(doc['href']).get_data(as_text=True)
            self.assertIn('<h1 class="search-entry-word">' + word + '</h1>', html)
            self.assertIn(doc['meaning'], html)
        stand = next(d for d in self.index.search('立つ') if d['kind'] == 'Word')
        self.assertNotIn('<h1>Dog</h1>', self.client.get(stand['href']).get_data(as_text=True))
        self.assertEqual(self.client.get('/search/entry/does-not-exist').status_code, 404)

    def test_kanji_links_and_examples_share_character_identity(self):
        catalog = {k['id']: k for k in K.KANJI_CATALOG}
        for k in K.KANJI_DATA:
            self.assertEqual(catalog[k['id']]['kanji'], k['kanji'])
            for w in k['vocab']:
                self.assertIn(k['kanji'], w['word'])
        for word in K.VOCAB_POOL:
            if word.get('kanji_id'):
                self.assertEqual(catalog[word['kanji_id']]['kanji'], word['kanji'])
        stand = catalog[K.KANJI_ID_BY_CHAR['水']]
        html = self.client.get('/kanji/' + str(stand['id'])).get_data(as_text=True)
        self.assertIn('<h1>' + stand['meaning'] + '</h1>', html)
        self.assertNotIn('It is a dog', html)

    def test_import_faults_are_gone_from_all_learning_pools(self):
        for source in (K.FREQUENCY_WORDS, K.EVERYDAY_WORDS, K.VOCAB_POOL, K.GRAMMAR_DATA):
            for word in source:
                self.assertFalse(re.search('[A-Za-z]', word.get('reading', '')), str(word.get('word', word.get('pattern'))))
        self.assertEqual(len(K.FREQUENCY_WORDS), 1999)
        self.assertEqual(len(K.PICTURE_DICT_WORDS), 582)
        self.assertFalse(any(d['word'] == '犬' and d['meaning'] == '77' for d in self.index.documents))
        do = [d for d in self.index.search('する') if d['word'] == 'する' and d['kind'] == 'Word']
        self.assertTrue(do)
        self.assertTrue(all(d['meaning'] != 'writer' for d in do))

    def test_conjugated_forms_have_correct_tense_and_context(self):
        for word, gloss in [('行きました', 'went'), ('立たない', 'do not stand'), ('立った', 'stood'), ('立てる', 'can stand')]:
            doc = next(d for d in self.index.search(word) if d['word'] == word and d['kind'] == 'Verb form')
            self.assertEqual(doc['meaning'], gloss)
            self.assertTrue(doc['form_label'])
        self.assertEqual(self.index.search('go')[0]['word'], '行く')

    def test_remaining_irregular_english_past_forms(self):
        for base,past in [('bend','bent'),('drive','drove'),('throw','threw')]:
            for verb in K.VERBS_DATA:
                if verb['meaning'].startswith('to '+base):
                    word=verb['forms']['past']['kanji']
                    doc=next(d for d in self.index.search(word) if d['word']==word and d['kind']=='Verb form')
                    self.assertTrue(doc['meaning'].startswith(past),doc['meaning'])

    def test_local_food_sentences_have_readings_and_english_translations(self):
        self.assertEqual(len(K.JAPAN_EXPLORER_DATA['food_words']), 47)
        for place in K.JAPAN_PLACES:
            s = place['situations']['beginner']
            self.assertFalse(re.search('[\u4e00-\u9fff]', s['reading']))
            self.assertFalse(re.search('[\u3040-\u30ff\u4e00-\u9fff]', s['en']))
        results = self.index.search('味噌ラーメンをください。')
        self.assertEqual(results[0]['meaning'], 'Please give me miso ramen.')


if __name__ == '__main__':
    unittest.main(verbosity=2)

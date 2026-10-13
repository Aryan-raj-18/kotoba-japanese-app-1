"""Rendered controls and API reading provenance, with unchanged lesson data."""
import json, os, sys, tempfile, unittest
os.environ['KOTOBA_DATA_DIR']=tempfile.mkdtemp(prefix='kotoba-speech-')
if os.environ.get('KOTOBA_TEST_PACKAGE'):
 sys.path.insert(0,os.environ['KOTOBA_TEST_PACKAGE']);import kotoba_app.app as K
else: import app as K
class SpeechReadingTests(unittest.TestCase):
 def setUp(self): self.c=K.app.test_client()
 def test_reading_notes_and_okurigana(self):
  self.assertEqual(K.kana_readings('ひと hito, ひと(つ) hito(tsu)'),['ひと','ひとつ'])
  self.assertEqual(K.kana_readings('し · On-yomi'),['し'])
 def test_all_flashcard_decks_have_readings(self):
  for deck in ['kanji','vocab','verbs','radicals','hiragana','katakana','N5','N4','N3','N2','N1']:
   for q in self.c.get('/api/flashcards_mcq?deck='+deck+'&count=60').json['questions']:
    self.assertTrue(q['reading'],(deck,q));self.assertNotIn(' · ',q['reading'])
   if not deck.startswith('N'):
    self.assertTrue(all(q['reading'] for q in self.c.get('/api/flashcards?deck='+deck).json['cards']))
 def test_roadmap_meaning_and_reading_questions_keep_kana(self):
  for ch in K.ROADMAP_CHAPTERS.values():
   if ch.get('kind')!='lesson' or ch.get('kana'): continue
   vocab={w['jp']:w['reading'] for w in ch.get('vocab',[])}
   cand=K._rm_candidates(ch)
   for typ in ['meaning','reading']:
    for q in cand[typ]:self.assertEqual(q['reading'],vocab[q['prompt']])
 def test_number_main_reading_and_individual_alternatives(self):
  e=next(x for x in K.KANJI_CATALOG if x['kanji']=='四')
  html=self.c.get('/kanji/'+str(e['id'])).get_data(as_text=True)
  self.assertIn('data-reading="し"',html)
  self.assertIn('data-speak="よん"',html)
  self.assertIn('data-reading="しがつ"',html)
 def test_roadmap_returns_have_stable_chapter_anchors(self):
  html=self.c.get('/roadmap').get_data(as_text=True)
  for cid in K.ROADMAP_CHAPTER_ORDER:
   self.assertIn('id="chapter-'+cid+'"',html)
   if K.ROADMAP_CHAPTERS[cid]['kind'] in ['lesson','review']:
    page=self.c.get('/roadmap/'+cid).get_data(as_text=True)
    self.assertIn('/roadmap#chapter-'+cid,page)
 def test_confirmed_name_reading_repair(self):
  for group in [K.KANJI_DATA,K.KANJI_CATALOG]:
   entry=next(x for x in group if x['kanji']=='名')
   self.assertEqual(K.kana_readings(entry['kun_yomi']),['な'])
   self.assertEqual(K.kana_readings(entry['on_yomi']),['メイ','ミョウ'])
 def test_existing_saved_readings_are_repaired_without_losing_the_list(self):
  old={'kind':'kanji','id':'名','front':'名','meaning':'name','reading':'さんねんまえ sannenmae, な na'}
  self.c.post('/api/favorites/toggle',json={'list':'Upgrade speech test','item':old})
  rows=self.c.get('/api/review/due?list=Upgrade%20speech%20test').json['items']
  self.assertEqual(len(rows),1);self.assertEqual(rows[0]['reading'],'な');self.assertEqual(rows[0]['meaning'],'name')
  numeral=K._normalize_number_vocab({'front':'四','reading':'よん'})
  self.assertEqual(numeral['reading'],'し')
 def test_search_entries_speak_their_own_reading(self):
  doc=next(d for d in K.SEARCH_INDEX.documents if d['word']=='空' and d['reading']=='そら') if hasattr(K,'SEARCH_INDEX') else None
  if doc is None:
   doc=next(d for d in K._get_search_index().documents if d['word']=='空' and d['reading']=='そら')
  html=self.c.get('/search/entry/'+doc['entry_id']).get_data(as_text=True)
  self.assertIn('data-reading="そら"',html)
if __name__=='__main__':unittest.main()

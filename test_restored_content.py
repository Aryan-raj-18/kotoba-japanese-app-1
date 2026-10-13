"""Protect complete level content and working quizzes against accidental removal."""
import os,tempfile,unittest,json,hashlib
from pathlib import Path
os.environ['KOTOBA_DATA_DIR']=tempfile.mkdtemp(prefix='kotoba-restored-')
import app as K
class RestoredCourseTests(unittest.TestCase):
 def setUp(self):self.client=K.app.test_client()
 def test_restored_datasets_match_saved_full_course(self):
  manifest=json.loads((Path(__file__).parent/'CONTENT_RESTORATION.json').read_text())
  for item in manifest['restored_datasets']:
   with self.subTest(dataset=item['file']):
    expected=item.get('current_sha256',item['sha256'])
    if item['file']=='roadmap.json':
     reorder=manifest['course_reordering'];expected=reorder['reordered_roadmap_sha256']
     self.assertEqual(reorder['source_roadmap_sha256'],item['sha256'])
     chapters={c['id']:c for sec in json.loads((K.CONTENT_DIR/'roadmap.json').read_text()) for c in sec['chapters']}
     self.assertEqual(set(chapters),set(reorder['preserved_chapters']))
     for key,c in chapters.items():
      data=c.copy()
      for field in reorder['allowed_chapter_metadata_changes'].get(key,[]):data.pop(field)
      digest=hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
      self.assertEqual(digest,reorder['preserved_chapters'][key])
    self.assertEqual(hashlib.sha256((K.CONTENT_DIR/item['file']).read_bytes()).hexdigest(),expected)
 def test_all_levels_have_kanji_and_working_practice(self):
  counts={'N5':103,'N4':174,'N3':393,'N2':410,'N1':911}
  for level,count in counts.items():
   with self.subTest(level=level):
    self.assertEqual(len(K.JLPT_BY_LEVEL[level]),count)
    for route in [f'/jlpt/{level}',f'/jlpt/{level}/practice',f'/jlpt/{level}/exam-practice',f'/jlpt/{level}/mock']:
     r=self.client.get(route);self.assertEqual(r.status_code,200,route)
     self.assertNotIn(b'Course preview',r.data,route)
    q=self.client.get('/api/jlpt_quiz',query_string={'level':level,'count':12}).get_json()['questions']
    self.assertEqual(len(q),12)
    by_kanji={e['kanji']:e for e in K.JLPT_BY_LEVEL[level]}
    for item in q:
     self.assertEqual(item['correct'],by_kanji[item['kanji']]['meaning'])
     self.assertIn(item['correct'],item['options']);self.assertEqual(len(set(item['options'])),4)
    cards=self.client.get('/api/flashcards',query_string={'deck':level,'count':12}).get_json()['cards']
    self.assertEqual(len(cards),12)
 def test_every_level_and_category_can_produce_exam_questions(self):
  counts={'N5':180,'N4':60,'N3':36,'N2':58,'N1':38}
  for level,count in counts.items():
   self.assertEqual(len(K.JLPT_EXAM_QUESTIONS[level]),count)
   for category in ['all',*K.JLPT_EXAM_CATEGORIES[level]]:
    with self.subTest(level=level,category=category):
     r=self.client.get('/api/jlpt_exam_quiz',query_string={'level':level,'category':category,'count':10})
     self.assertEqual(r.status_code,200);self.assertTrue(r.json['questions'])
     for q in r.json['questions']:
      self.assertEqual(q['options'][q['answer_index']],q['answer'])
      if category!='all':self.assertEqual(q['category'],category)
 def test_full_roadmap_is_unlocked_and_advanced_lessons_are_completable(self):
  self.assertEqual(len(K.ROADMAP_CHAPTERS),91)
  for chapter in K.ROADMAP_CHAPTERS.values():
   self.assertFalse(chapter.get('planned'),chapter['id'])
   self.assertNotEqual(K._roadmap_chapter_status(chapter['id'],set()),'locked')
   if chapter.get('kind')=='lesson':self.assertTrue(chapter.get('vocab'),chapter['id'])
  for chapter_id in ['n1-grammar-01','n2-grammar-01','n3-grammar-01']:
   r=self.client.get('/roadmap/'+chapter_id)
   self.assertEqual(r.status_code,200);self.assertNotIn(b'Course preview',r.data)
   self.assertEqual(self.client.post('/api/roadmap/complete',json={'chapter_id':chapter_id}).status_code,200)
 def test_other_restored_sections_are_populated(self):
  for source,minimum in [(K.GRAMMAR_DATA,229),(K.STORIES_DATA,19),(K.CONVERSATIONS_DATA,50),(K.FREQUENCY_WORDS,1999),(K.PICTURE_DICT_WORDS,582),(K.KANJI_CATALOG,2103)]:self.assertGreaterEqual(len(source),minimum)
if __name__=='__main__':unittest.main(verbosity=2)

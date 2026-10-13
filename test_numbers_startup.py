"""Numbers and server lifecycle regressions, using the packaged Android module."""
import os,sys,tempfile,unittest,threading,copy
from pathlib import Path
from unittest.mock import patch,Mock
os.environ['KOTOBA_DATA_DIR']=tempfile.mkdtemp(prefix='kotoba-startup-')
sys.path.insert(0,os.environ.get('KOTOBA_TEST_PACKAGE',str(Path(__file__).parent/'android/app/src/main/python')))
import kotoba_app.app as K

def numeral(entry):return entry.get('kanji') or entry.get('front') or entry.get('word') or entry.get('jp')
def numbers_first(values):return sorted(values,key=lambda e:0 if isinstance(e,dict) and numeral(e) in K.NUMBER_ON_READINGS else 1)
class Numbers(unittest.TestCase):
 def setUp(self):self.client=K.app.test_client()
 def test_all_numeric_practice_questions_use_on_yomi(self):
  numbers=[w for w in K.PRACTICE_POOL if w['kanji'] in K.NUMBER_ON_READINGS];self.assertGreaterEqual(len(numbers),10)
  with patch.object(K.random,'choice',return_value='reading'):
   for w in numbers:
    q=self.client.get('/api/practice/quiz/'+str(w['kanji_id'])+'?mode=kanji').get_json()
    self.assertEqual(q['correct_word'],K.NUMBER_ON_READINGS[w['kanji']][0]);self.assertIn('on-yomi',q['question']);self.assertIn(q['correct_word'],q['options']);self.assertEqual(len(q['options']),len(set(q['options'])))
 def test_numeric_classic_and_mcq_cards(self):
  with patch.object(K.random,'shuffle',side_effect=lambda x:x.sort(key=lambda e:0 if isinstance(e,dict) and numeral(e) in K.NUMBER_ON_READINGS else 1)),patch.object(K.random,'sample',side_effect=lambda x,n:numbers_first(x)[:n]):
   for route in ['/api/flashcards?deck=kanji&count=60','/api/flashcards_mcq?deck=kanji&count=60','/api/flashcards_mcq?deck=N5&count=60']:
    data=self.client.get(route).get_json();cards=data.get('cards',data.get('questions',[]));found=[c for c in cards if numeral(c) in K.NUMBER_ON_READINGS];self.assertGreaterEqual(len(found),10,(route,data.keys()))
    for card in found:self.assertEqual(card['sub'],K.NUMBER_ON_READINGS[numeral(card)][0]+' · On-yomi')
 def test_placement_numbers(self):
  with patch.object(K.random,'choice',side_effect=lambda x:numbers_first(x)[0]):questions=K._placement_questions()
  found=[q for q in questions if q.get('type')=='Kanji' and q.get('prompt') in K.NUMBER_ON_READINGS];self.assertTrue(found)
  for q in found:self.assertEqual(q['sub'],K.NUMBER_ON_READINGS[q['prompt']][0]+' · On-yomi')
 def test_vocabulary_and_recursive_lesson_copies(self):
  found=0
  for pool in [K.ALL_WORDS,K.VOCAB_POOL,K.EVERYDAY_WORDS,K.FREQUENCY_WORDS]:
   for w in pool:
    word=w.get('word') or w.get('jp')
    if word in K.NUMBER_ON_READINGS:found+=1;self.assertEqual(w['reading'],K.NUMBER_ON_READINGS[word][0])
  self.assertGreaterEqual(found,10)
  lesson={'lesson':[{'jp':'四','reading':'よん'},{'word':'七','reading':'なな'}]};K._normalize_number_vocab(lesson);self.assertEqual([w['reading'] for w in lesson['lesson']],['し','しち'])
 def test_counters_dates_and_non_numeric_readings_unchanged(self):
  words=[{'word':w,'reading':r} for w,r in [('一つ','ひとつ'),('二つ','ふたつ'),('一人','ひとり'),('二人','ふたり'),('一日','ついたち')]];before=copy.deepcopy(words);K._normalize_number_vocab(words);self.assertEqual(words,before)
  self.assertEqual(K.first_reading({'kanji':'木','kun_yomi':'き','on_yomi':'モク'}),'き')
  four=next(w for w in K.KANJI_CATALOG if w['kanji']=='四');self.assertTrue(four.get('kun_yomi'))
 def test_search_numeric_kanji_display(self):
  index=K._search.build_index(vars(K));found=[d for d in index.documents if d['kind']=='Kanji' and d['word'] in K.NUMBER_ON_READINGS];self.assertGreaterEqual(len(found),10)
  for d in found:self.assertEqual(d['reading'],K.NUMBER_ON_READINGS[d['word']][0]+' · On-yomi')
class Startup(unittest.TestCase):
 def setUp(self):self.assertFalse(K._server_running)
 def test_failed_bind_remains_retryable(self):
  with patch('werkzeug.serving.make_server',side_effect=OSError('occupied')) as make:
   for _ in range(2):
    with self.assertRaises(OSError):K.run_server()
    self.assertFalse(K._server_running)
   self.assertEqual(make.call_count,2)
 def test_system_exit_does_not_mark_server_running(self):
  with patch('werkzeug.serving.make_server',side_effect=SystemExit(1)):
   with self.assertRaises(SystemExit):K.run_server()
  self.assertFalse(K._server_running)
 def test_worker_failure_can_restart(self):
  first=Mock();first.serve_forever.side_effect=RuntimeError('worker failed');second=Mock()
  with patch('werkzeug.serving.make_server',side_effect=[first,second]):
   with self.assertRaises(RuntimeError):K.run_server()
   self.assertFalse(K._server_running);K.run_server()
  first.server_close.assert_called_once();second.server_close.assert_called_once();self.assertFalse(K._server_running)
 def test_concurrent_activity_reuses_live_server(self):
  entered=threading.Event();release=threading.Event();server=Mock()
  def serve():entered.set();release.wait(5)
  server.serve_forever.side_effect=serve
  with patch('werkzeug.serving.make_server',return_value=server) as make:
   worker=threading.Thread(target=K.run_server);worker.start()
   try:self.assertTrue(entered.wait(2));K.run_server();self.assertEqual(make.call_count,1)
   finally:release.set();worker.join(5)
  self.assertFalse(worker.is_alive());self.assertFalse(K._server_running);server.server_close.assert_called_once()
 def test_cleanup_failure_still_clears_running_flag(self):
  server=Mock();server.server_close.side_effect=OSError('close failed')
  with patch('werkzeug.serving.make_server',return_value=server):
   with self.assertRaises(OSError):K.run_server()
  self.assertFalse(K._server_running)
 def test_new_native_sessions_health_and_authorization(self):
  with patch.dict(os.environ,{'KOTOBA_NATIVE_TOKEN':'test-native-token'}):
   for _ in range(3):
    client=K.app.test_client();self.assertEqual(client.get('/__health').get_json(),{'app':'Kotoba','version':'1.0.0'});self.assertEqual(client.get('/__bootstrap?token=wrong').status_code,403);self.assertEqual(client.get('/__bootstrap?token=test-native-token',follow_redirects=True).status_code,200);self.assertEqual(client.get('/api/backup/data').status_code,200)
 def test_reopening_keeps_saved_progress(self):
  with patch.dict(os.environ,{'KOTOBA_NATIVE_TOKEN':'test-native-token'}):
   first=K.app.test_client();first.get('/__bootstrap?token=test-native-token');first.post('/api/learner/record',json={'id':'one','front':'一','correct':True,'quality':4});before=first.get('/api/backup/data').get_json()
   second=K.app.test_client();second.get('/__bootstrap?token=test-native-token');after=second.get('/api/backup/data').get_json()
   self.assertEqual(before['learner'],after['learner']);self.assertEqual(before['progress'],after['progress'])
if __name__=='__main__':unittest.main(verbosity=2)

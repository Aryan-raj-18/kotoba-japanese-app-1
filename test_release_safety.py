"""Regression tests for real corruption, malformed requests and deletion bugs."""
import os,tempfile,json,copy,unittest,sys
from pathlib import Path
from unittest.mock import patch
os.environ['KOTOBA_DATA_DIR']=tempfile.mkdtemp(prefix='kotoba-safety-')
if os.environ.get("KOTOBA_TEST_PACKAGE"):
 sys.path.insert(0,os.environ["KOTOBA_TEST_PACKAGE"])
 import kotoba_app.app as K
else:
 import app as K
class ReleaseTests(unittest.TestCase):
 def setUp(self):
  self.directory=tempfile.TemporaryDirectory();K.DATA_DIR=Path(self.directory.name)
  for name in dir(K):
   value=getattr(K,name)
   if name.isupper() and name.endswith(('_FILE','_PATH')) and isinstance(value,Path):setattr(K,name,K.DATA_DIR/value.name)
  self.client=K.app.test_client();self.client.get('/data-controls')
 def tearDown(self):self.directory.cleanup()
 def export(self,client=None):
  data=(client or self.client).get('/api/backup/data').get_json();data.pop('created',None);return data
 def test_malformed_requests_do_not_mutate_state(self):
  before=self.export()
  bad=[('/api/practice/new_session',{'count':'bad'}),('/api/learner/action',{'action':'audio','amount':'bad'}),('/api/learner/action',{'action':'audio','amount':1000000000}),('/api/favorites/list',{'name':[]}),('/api/feedback',[]),('/api/learner/record',{'correct':'false'}),('/api/favorites/toggle',{'item':[]} ),('/api/roadmap/start',{'chapter_id':[]})]
  for route,payload in bad:
   with self.subTest(route=route,payload=payload):self.assertEqual(self.client.post(route,json=payload).status_code,400)
  self.assertEqual(before,self.export())
 def test_bad_backup_does_not_break_home_or_progress(self):
  self.client.post('/api/learner/record',json={'id':12,'front':'水','correct':True,'quality':4})
  before=self.export()
  for learner in [{'xp':'bad'},{'srs':{'x':{'next_review':[]}}},{'srs':{'x':{'mastery':{}}}},{'lists':{'Favorites':[1]}}]:
   response=self.client.post('/api/backup/data',json={'format':'kotoba-backup-v1','learner':learner})
   self.assertEqual(response.status_code,400);self.assertEqual(before,self.export());self.assertEqual(self.client.get('/').status_code,200)
 def test_legacy_boolean_history_and_valid_backup_restore(self):
  self.client.post('/api/learner/record',json={'id':'one','front':'一','correct':True,'quality':4})
  data=self.export();data['learner']['history'][0]['correct']=True
  self.assertEqual(self.client.post('/api/backup/data',json=data).status_code,200)
  self.assertEqual(self.export()['learner']['reviews'],1)
 def test_failed_restore_rolls_back_earlier_writes(self):
  self.client.post('/api/learner/action',json={'action':'audio'})
  before=self.export();replacement=copy.deepcopy(before);replacement['learner']['xp']=999;replacement['progress']={'kanji':['1']}
  atomic=K._safety.atomic_json
  def fail(path,value):
   if Path(path)==K.PROGRESS_FILE:raise OSError('simulated disk failure')
   return atomic(path,value)
  with patch.object(K._safety,'atomic_json',side_effect=fail):self.assertEqual(self.client.post('/api/backup/data',json=replacement).status_code,500)
  self.assertEqual(before,self.export());self.assertEqual(self.client.get('/').status_code,200)
 def test_reset_requires_confirmation_and_removes_state(self):
  self.client.post('/api/learner/action',json={'action':'speaking'})
  self.assertEqual(self.client.post('/api/profile/reset',json={'confirm':'RESET'}).status_code,400)
  with self.client.session_transaction() as session:token=session['csrf_token']
  self.assertEqual(self.client.post('/api/profile/reset',json={'confirm':'RESET','csrf_token':token}).status_code,200)
  self.assertEqual(self.export()['learner']['xp'],0)
 def test_preview_is_open_but_not_completable(self):
  with patch.dict(K.ROADMAP_CHAPTERS['n1-grammar-01'],{'planned':True}):
   self.assertIn(b'preview',self.client.get('/roadmap/n1-grammar-01').data)
   self.assertEqual(self.client.post('/api/roadmap/complete',json={'chapter_id':'n1-grammar-01'}).status_code,400)
 def test_privacy_and_controls_available(self):
  for route in ['/privacy','/data-controls','/backup']:self.assertEqual(self.client.get(route).status_code,200)
 def test_available_reviews_have_questions(self):
  for section in K.ROADMAP:
   for chapter in section['chapters']:
    if chapter.get('kind')=='review':
     scope=chapter.get('scope','all')
     questions=K._build_mixed_quiz() if scope=='all' else K._build_section_quiz(scope)
     if not questions:
      self.assertTrue(chapter.get('planned'))
      self.assertIn(b'preview',self.client.get('/roadmap/'+chapter['id']).data)
      self.assertEqual(self.client.post('/api/roadmap/complete',json={'chapter_id':chapter['id']}).status_code,400)
 def seed_legacy(self):
  K._save_users([{'id':1,'username':'alice','password_hash':'old-hash'}, {'id':2,'username':'bruno','password_hash':'old-hash'}])
  for uid in [1,2]:
   K._learner.record_action(K.DATA_DIR,{'id':uid},'speaking',uid)
 def select(self,uid):
  with self.client.session_transaction() as session:token=session['csrf_token']
  return self.client.post('/api/study-record/select',json={'id':uid,'csrf_token':token})
 def test_login_and_signup_are_removed_and_content_still_accessible(self):
  for route in ['/login','/signup','/logout']:
   for method in ['get','post']:
    self.assertEqual(getattr(self.client,method)(route).status_code,404)
  for route in ['/','/data-controls','/backup','/about','/japan','/roadmap','/jlpt/N1']:
   response=self.client.get(route);self.assertEqual(response.status_code,200)
   for target in [b'href="/login"',b'href="/signup"',b'action="/logout"']:
    self.assertNotIn(target,response.data)
  self.assertFalse(K.USERS_FILE.exists())
 def test_previous_study_data_survives_cookie_expiry_and_switching(self):
  self.client.post('/api/learner/action',json={'action':'audio'})
  guest=self.export();self.seed_legacy()
  self.assertEqual(self.select(1).status_code,200)
  alice=self.export();self.assertGreater(alice['learner']['xp'],0)
  fresh=K.app.test_client();self.assertEqual(self.export(fresh),alice)
  self.assertEqual(self.select(2).status_code,200)
  self.assertEqual(self.select('device').status_code,200);self.assertEqual(self.export(),guest)
  self.assertEqual(self.select(1).status_code,200);self.assertEqual(self.export(),alice)
 def test_upgrade_preserves_active_previous_study_record(self):
  self.seed_legacy();K.DEVICE_LEARNER_FILE.unlink(missing_ok=True)
  with self.client.session_transaction() as session:session['user_id']=2
  self.client.get('/')
  self.assertEqual(json.loads(K.DEVICE_LEARNER_FILE.read_text()),{'legacy_id':2})
  fresh=K.app.test_client();self.assertEqual(self.export(fresh),self.export())
 def test_saved_study_selection_requires_csrf_and_known_id(self):
  self.seed_legacy();before=self.export()
  self.assertEqual(self.client.post('/api/study-record/select',json={'id':1}).status_code,400)
  for uid in [True,{},[],999,'1']:self.assertEqual(self.select(uid).status_code,400)
  self.assertEqual(self.export(),before)
 def test_previous_study_deletion_preserves_other_record_and_device(self):
  self.client.post('/api/learner/action',json={'action':'audio'});guest=self.export();self.seed_legacy()
  self.assertEqual(self.select(2).status_code,200)
  with self.client.session_transaction() as session:token=session['csrf_token']
  self.assertEqual(self.client.post('/api/profile/delete',json={'confirm':'DELETE','csrf_token':token}).status_code,200)
  self.assertEqual([u['username'] for u in K._load_users()],['alice'])
  saved=json.loads((K.DATA_DIR/'user_learner_state.json').read_text())
  self.assertIn('1',saved);self.assertNotIn('2',saved)
  self.assertEqual(self.export(),guest)
 def test_android_session_is_required_without_user_login(self):
  with patch.dict(os.environ,{'KOTOBA_NATIVE_TOKEN':'release-session'}):
   self.assertEqual(self.client.get('/api/backup/data').status_code,403)
   self.assertEqual(self.client.get('/__health').status_code,200)
   self.assertEqual(self.client.get('/__bootstrap?token=wrong').status_code,403)
   self.assertEqual(self.client.get('/__bootstrap?token=release-session').status_code,302)
   self.assertEqual(self.client.get('/api/backup/data').status_code,200)
   self.assertEqual(self.client.get('/login').status_code,404)
   self.assertEqual(self.client.get('/api/backup/data').status_code,200)
 def test_corrupt_local_counters_recover(self):
  K._safety.atomic_json(K.DATA_DIR/'learner_state.json',{'xp':'bad','reviews':[], 'srs':{'x':{'next_review':[], 'mastery':{}}}})
  self.assertEqual(self.client.get('/').status_code,200);self.assertEqual(self.client.get('/api/learner/summary').status_code,200)
if __name__=='__main__':unittest.main(verbosity=2)

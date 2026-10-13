import json,os,tempfile,unittest
from pathlib import Path
os.environ['KOTOBA_DATA_DIR']=tempfile.mkdtemp()
if os.environ.get('KOTOBA_TEST_PACKAGE'):
 import sys
 sys.path.insert(0,os.environ['KOTOBA_TEST_PACKAGE'])
 from kotoba_app.app import app,JLPT_KANJI,KANJI_ID_BY_CHAR
else:
 from app import app,JLPT_KANJI,KANJI_ID_BY_CHAR
ROOT=Path(__file__).parent
class NotificationCatalogTests(unittest.TestCase):
 def test_every_level_has_exact_public_content(self):
  with app.test_client() as c:
   for level in ['N5','N4','N3','N2','N1']:
    result=c.get('/api/kanji-notification/catalog?level='+level);self.assertEqual(result.status_code,200)
    cards=result.json['cards'];expected=[e for e in JLPT_KANJI if e['level']==level]
    self.assertEqual(len(cards),len(expected))
    for card,original in zip(cards,expected):
     self.assertEqual(card,dict(id=KANJI_ID_BY_CHAR[original['kanji']],kanji=original['kanji'],meaning=original['meaning'],on=original.get('on_yomi',''),kun=original.get('kun_yomi',''),level=level))
 def test_unknown_level_is_rejected(self):
  with app.test_client() as c:self.assertEqual(c.get('/api/kanji-notification/catalog?level=N0').status_code,400)
 def test_native_offline_catalog_matches_all_levels(self):
  native=json.loads((ROOT/'android/app/src/main/assets/kanji-notification.json').read_text())
  with app.test_client() as c:
   self.assertEqual(native,sum([c.get('/api/kanji-notification/catalog?level='+l).json['cards'] for l in ['N5','N4','N3','N2','N1']],[]))
  self.assertEqual(len(native),1991);self.assertEqual(len({x['id'] for x in native}),1991)
 def test_screen_and_links_are_present(self):
  with app.test_client() as c:
   html=c.get('/kanji-notification').data.decode();self.assertIn('kanji-notification-mode',html);self.assertIn('kanji-notification.js',html)
   html=c.get('/kanji/'+str(KANJI_ID_BY_CHAR['日'])).data.decode();self.assertIn('Show this kanji in a notification',html)
 def test_no_additional_privileged_permission(self):
  manifest=(ROOT/'android/app/src/main/AndroidManifest.xml').read_text()
  for perm in ['SCHEDULE_EXACT_ALARM','USE_EXACT_ALARM','SYSTEM_ALERT_WINDOW','FOREGROUND_SERVICE']:
   self.assertNotIn(perm,manifest)
  self.assertIn('KanjiNotificationReceiver',manifest);self.assertIn('MY_PACKAGE_REPLACED',manifest)
if __name__=='__main__':unittest.main()

from test_android_mirror_helpers import expected_native
from pathlib import Path
import unittest
R=Path(__file__).resolve().parent
class WaterGlass43(unittest.TestCase):
 def test_toggle_and_persistence(self):
  js=(R/'static/js/liquid-glass.js').read_text()
  self.assertIn("localStorage.setItem(KEY",js)
  self.assertIn("root.setAttribute('data-glass'",js)
  self.assertIn('Liquid Glass',(R/'templates/base.html').read_text())
 def test_jlpt_panel_artifacts(self):
  css=(R/'static/css/liquid-glass.css').read_text()
  self.assertIn('.exam-practice-stage > .exam-stage-panel:is(#exam-panel-intro,#exam-panel-results)',css)
  self.assertRegex(css,r'backdrop-filter:\s*none\s*!important')
 def test_synced(self):
  for r in ['app.py','static/css/liquid-glass.css','static/sw.js','templates/base.html']:
   self.assertEqual(expected_native(R,r),(R/'android/app/src/main/python/kotoba_app'/r).read_bytes())
if __name__=='__main__': unittest.main()

from test_android_mirror_helpers import expected_native
"""Build 42: regression for removal of doubled rectangular glass plates."""
import unittest
from pathlib import Path
R=Path(__file__).resolve().parent
class GlassSurface42(unittest.TestCase):
  def test_only_real_visible_cards_are_glass(self):
    css=(R/'static/css/liquid-glass.css').read_text()
    self.assertIn('.practice-stage, .game-stage',css)
    self.assertIn('.flash-mode, .flashcard',css)
    self.assertIn('background: transparent !important',css)
    self.assertIn('.exam-quiz-card',css)
    self.assertIn('.japan-how > div',css)
    self.assertIn('.flash-face',css)
    self.assertIn('.modal-overlay > .modal-card',css)
  def test_no_svg_distortion_pseudoplates(self):
    css=(R/'static/css/liquid-glass.css').read_text()
    js=(R/'static/js/liquid-glass.js').read_text()
    self.assertNotIn('filter: url(',css)
    self.assertNotIn('createElementNS',js)
    self.assertNotIn('pointermove',js)
    self.assertIn('content: none !important',css)
  def test_compatibility_and_android_mirror(self):
    css=(R/'static/css/liquid-glass.css').read_text()
    self.assertIn('prefers-reduced-transparency: reduce',css)
    self.assertIn('data-glass-quality="lite"',css)
    self.assertRegex((R/'app.py').read_text(),r'ASSET_BUILD = "[0-9]+"')
    self.assertIn('kotoba-shell-v100-build'+__import__('re').search(r'ASSET_BUILD = "(\d+)"',(R/'app.py').read_text()).group(1),(R/'static/sw.js').read_text())
    for rel in ('app.py','static/sw.js','static/css/liquid-glass.css','static/js/liquid-glass.js','templates/base.html'):
      self.assertEqual(expected_native(R,rel),(R/'android/app/src/main/python/kotoba_app'/rel).read_bytes())
if __name__=='__main__': unittest.main()

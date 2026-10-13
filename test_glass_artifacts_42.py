"""Build 42: regressions for JLPT ghost panels, nav overlays, flashcards, and accessibility."""
import unittest
from pathlib import Path
ROOT=Path(__file__).parent
class GlassArtifactTests(unittest.TestCase):
    def test_css_valid_and_single_source(self):
        css=(ROOT/'static/css/liquid-glass.css').read_text()
        self.assertEqual(css.count('{'),css.count('}'))
        self.assertLess(len(css.splitlines()),400, 'Old layered build CSS has returned')
    def test_jlpt_wrappers_are_not_glass(self):
        css=(ROOT/'static/css/liquid-glass.css').read_text()
        self.assertIn('.practice-stage, .game-stage',css)
        self.assertIn('.flash-mode, .flashcard',css)
        self.assertIn('background: transparent !important',css)
        self.assertIn(':has(:is(.quiz-card,.learn-card',css)
        self.assertIn('.quiz-card',css)
    def test_no_dynamic_overlay_or_displacement_filter(self):
        js=(ROOT/'static/js/liquid-glass.js').read_text()
        css=(ROOT/'static/css/liquid-glass.css').read_text()
        for forbidden in ('createElementNS','insertBefore(', 'feDisplacementMap', 'pointermove'):
            self.assertNotIn(forbidden,js)
        self.assertNotIn('filter: url(',css)
    def test_more_sections_and_ios_fallback(self):
        css=(ROOT/'static/css/liquid-glass.css').read_text()
        for cls in ('.speaking-card','.story-body','.japan-map-card','.japan-how > div',
                    '.write-panel','.jlpt-level-card','.kana-tile','.flash-face',
                    '.modal-card','.settings-panel','.review-card'):
            self.assertIn(cls,css)
        self.assertIn('prefers-reduced-transparency: reduce',css)
        self.assertIn('data-glass-quality="lite"',css)
if __name__=='__main__':unittest.main()

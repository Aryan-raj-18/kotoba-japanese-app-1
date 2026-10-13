from test_android_mirror_helpers import expected_native
"""Regression guards for the whole-app liquid-glass finish and header filter leak."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
ANDROID = ROOT/'android/app/src/main/python/kotoba_app'
class WholeAppGlassTests(unittest.TestCase):
    def test_no_displacement_on_header_or_footer(self):
        js=(ROOT/'static/js/liquid-glass.js').read_text()
        css=(ROOT/'static/css/liquid-glass.css').read_text()
        self.assertNotIn('createElementNS', js)
        self.assertNotIn('filter: url(#', css)
        self.assertIn('.site-header::before', css)
        self.assertIn('.kotoba-bottom-nav::after', css)
        self.assertIn('.settings-panel', css)
        self.assertIn('.practice-stage, .game-stage', css)

    def test_every_feature_has_a_glass_surface(self):
        css=(ROOT/'static/css/liquid-glass.css').read_text()
        for cls in ('stage-panel','practice-stage','game-stage','grammar-detail-card',
                    'story-body','story-line','vocab-table','category-block','write-panel',
                    'sub-panel','japan-map-card','japan-train-panel','jlpt-entry-card',
                    'rm-panel','rm-section-banner','kanji-card','kana-tile','rad-card',
                    'search-entry-panel','review-card','speaking-card','achievement-card',
                    'backup-card','favorite-card','mission-card','settings-panel'):
            with self.subTest(cls=cls): self.assertIn('.'+cls, css)
    def test_all_page_templates_have_glass_styled_content(self):
        css=(ROOT/'static/css/liquid-glass.css').read_text()
        covered_classes=set(['page-head', 'journey-hero', 'continue-card', 'stage-panel', 'practice-stage', 'game-stage', 'story-body', 'convo', 'category-block', 'path-card', 'grammar-detail-card', 'kanji-card', 'kana-tile', 'rad-card', 'rm-panel', 'rm-section-banner', 'speak-card', 'speaking-card', 'story-card', 'jlpt-level-card', 'jlpt-entry-card', 'japan-map-card', 'japan-hero', 'search-entry-panel', 'search-result-card', 'about-card', 'feedback-form', 'backup-card', 'favorite-list-block', 'mistake-card', 'write-panel', 'sub-panel', 'learner-stat', 'achievement-card', 'detail-info', 'rad-panel', 'flashcard', 'quiz-card', 'review-card'])
        pages=sorted(p for p in (ROOT/'templates').glob('*.html')
                     if p.name!='base.html' and not p.name.startswith('_'))
        self.assertGreaterEqual(len(pages), 40)
        for page in pages:
            with self.subTest(template=page.name):
                found=set()
                for match in re.findall(r'class="([^"\n]+)"',page.read_text()):
                    found.update(match.split())
                matches={cls for cls in found & covered_classes if '.'+cls in css}
                self.assertTrue(matches, f'{page.name} has no glass-styled page content')
    def test_synced_android_assets(self):
        for rel in ('app.py','static/css/liquid-glass.css','static/js/liquid-glass.js','static/sw.js'):
            with self.subTest(rel=rel):
                self.assertEqual(expected_native(ROOT,rel),(ANDROID/rel).read_bytes())
if __name__=='__main__': unittest.main()

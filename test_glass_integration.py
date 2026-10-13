from test_android_mirror_helpers import expected_native
"""No third-party packages needed: deployment/compatibility regression checks."""
import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / 'android/app/src/main/python/kotoba_app'

class GlassIntegration(unittest.TestCase):
    def test_no_artifact_producing_displacement_is_active(self):
        js = (ROOT/'static/js/liquid-glass.js').read_text()
        css = (ROOT/'static/css/liquid-glass.css').read_text()
        self.assertNotIn('feDisplacementMap', js)
        self.assertNotIn('createFilters(', js)
        self.assertNotIn('createElementNS', js)
        self.assertNotIn('filter: url(#kotoba-liquid-displacement)', css)
        self.assertIn('--liquid-blur: blur(', css); self.assertIn('backdrop-filter: var(--liquid-blur)', css)
        self.assertIn('liquid-glass-react', js)  # MIT attribution kept
        self.assertTrue((ROOT/'static/vendor/liquid-glass-react/LICENSE').exists())

    def test_only_two_theme_modes_and_stored_preference_migration(self):
        catalog = (ROOT/'static/js/theme-catalog.js').read_text()
        raw = re.search(r'const themes=(\[.*?\]);', catalog).group(1)
        themes = json.loads(raw)
        self.assertEqual({t['id'] for t in themes}, {'sakura-journey','kyoto-night'})
        self.assertIn('darkLegacy', catalog)
        self.assertIn('lightLegacy', catalog)
        self.assertIn("return 'auto'", catalog)
        self.assertNotIn('More palettes', (ROOT/'templates/base.html').read_text())

    def test_main_android_source_are_exact_mirrors(self):
        for rel in ['app.py','templates/base.html','static/js/theme-catalog.js','static/js/theme.js',
                    'static/js/liquid-glass.js','static/css/style.css','static/css/ui-shell.css',
                    'static/css/journey.css','static/css/liquid-glass.css','static/sw.js']:
            with self.subTest(file=rel):
                self.assertEqual(expected_native(ROOT,rel), (PACKAGE/rel).read_bytes())
        self.assertEqual((ROOT/'static/vendor/liquid-glass-react/LICENSE').read_bytes(),
                         (PACKAGE/'static/vendor/liquid-glass-react/LICENSE').read_bytes())

    def test_offline_cache_points_to_existing_assets(self):
        text = (ROOT/'static/sw.js').read_text()
        for asset in re.findall(r'^\s*"(/static/[^"\n]+)"', text, flags=re.M):
            self.assertTrue((ROOT/asset.lstrip('/')).exists(), asset)
        self.assertIn('/static/js/liquid-glass.js', text)
        self.assertNotIn('/static/themes/water-glass.svg', text)

if __name__ == '__main__':unittest.main()

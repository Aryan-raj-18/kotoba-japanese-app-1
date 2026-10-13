"""Cache only versioned public assets; preserve fresh local study pages."""
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

os.environ['KOTOBA_DATA_DIR'] = tempfile.mkdtemp(prefix='kotoba-assets-')
sys.path.insert(0, os.environ.get('KOTOBA_TEST_PACKAGE', str(Path(__file__).parent / 'android/app/src/main/python')))
from kotoba_app.app import app


class Loading(unittest.TestCase):
    def test_assets_have_cache_lifetime_and_pages_do_not(self):
        c = app.test_client()
        page = c.get('/kanji')
        try:
            html = page.get_data(as_text=True)
        finally:
            page.close()
        match = re.search(r'src="(/static/js/kanji_list\.js\?v=\d+)"', html)
        self.assertIsNotNone(match, 'Kanji page should include a versioned kanji_list.js asset')
        asset = c.get(match.group(1))
        try:
            self.assertEqual(asset.status_code, 200)
            self.assertIn('max-age=31536000', asset.headers['Cache-Control'])
        finally:
            asset.close()
        for route in ['/', '/kanji', '/api/learner/summary']:
            response = c.get(route)
            try:
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
            finally:
                response.close()

    def test_page_script_order_is_deferred_after_early_theme(self):
        response = app.test_client().get('/kanji')
        try:
            html = response.get_data(as_text=True)
        finally:
            response.close()
        # Cache version changes must not break script presence/order checks.
        self.assertRegex(html, r'<script src="/static/js/theme-catalog\.js\?v=\d+"></script>')
        self.assertIn('<script defer src=', html)
        self.assertLess(html.index('js/theme-catalog.js'), html.index('<script defer src='))
        self.assertLess(html.index('js/search-match.js'), html.index('js/kanji_list.js'))
        self.assertNotIn('<script defer src="/static/js/theme-catalog.js', html)

    def test_native_worker_avoids_duplicate_precache_and_json_is_safe(self):
        from kotoba_app.app import _catalog_metadata
        response = app.test_client().get('/')
        try:
            html = response.get_data(as_text=True)
        finally:
            response.close()
        self.assertIn('if (window.KotobaStartupNative)', html)
        self.assertIn('getRegistrations()', html)
        for kind in ['kanji', 'everyday']:
            self.assertNotIn('<', _catalog_metadata(kind))


if __name__ == '__main__':
    unittest.main()

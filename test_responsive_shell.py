from test_android_mirror_helpers import expected_native
"""Fast no-dependency regressions for the desktop settings sheet and mobile shell."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
ANDROID = ROOT / 'android/app/src/main/python/kotoba_app'


class ResponsiveShellTests(unittest.TestCase):
    def test_desktop_settings_dropdown_owns_scrolling(self):
        style = (ROOT / 'static/css/style.css').read_text(encoding='utf8')
        panel = re.search(r'\.settings-panel\s*\{(.*?)\}', style, re.S)
        self.assertIsNotNone(panel)
        rules = panel.group(1)
        self.assertRegex(rules, r'max-height\s*:\s*calc\(100dvh\s*-\s*112px\)')
        self.assertRegex(rules, r'overflow-y\s*:\s*auto')
        self.assertRegex(rules, r'overscroll-behavior\s*:\s*contain')
        sheet = re.search(r'@media \(max-width: 560px\)\s*\{\s*\.settings-panel\s*\{(.*?)\}', style, re.S)
        self.assertIsNotNone(sheet)
        self.assertIn('max-height: 80dvh', sheet.group(1))
        self.assertIn('overflow-y: auto', sheet.group(1))
        html = (ROOT / 'templates/base.html').read_text(encoding='utf8')
        self.assertRegex(html, r'id="settings-panel"[^>]*tabindex="0"')

    def test_mobile_shell_fills_screen_without_overlaying_system_bars(self):
        shell = (ROOT / 'static/css/ui-shell.css').read_text(encoding='utf8')
        self.assertIn('margin: 4px 4px 0;', shell)
        self.assertIn('width: calc(100% - 8px)', shell)
        self.assertIn('left: max(4px, env(safe-area-inset-left, 0px));', shell)
        self.assertIn('right: max(4px, env(safe-area-inset-right, 0px));', shell)
        self.assertIn('bottom: calc(4px + env(safe-area-inset-bottom, 0px));', shell)
        kotlin = (ROOT / 'android/app/src/main/java/com/kotoba/app/MainActivity.kt').read_text(encoding='utf8')
        self.assertIn('view.setPadding(safe.left, safe.top, safe.right, safe.bottom)', kotlin)

    def test_android_sources_and_cache_bust_are_synchronized(self):
        for source in ('app.py', 'templates/base.html', 'static/css/style.css', 'static/css/ui-shell.css', 'static/sw.js'):
            with self.subTest(source=source):
                self.assertEqual(expected_native(ROOT,source), (ANDROID/source).read_bytes())
        version = re.search(r'ASSET_BUILD = "(\d+)"', (ROOT/'app.py').read_text()).group(1)
        sw = (ROOT/'static/sw.js').read_text()
        self.assertIn(f'kotoba-shell-v100-build{version}', sw)
        self.assertIn(f'"?v={version}"', sw)


if __name__ == '__main__':
    unittest.main()

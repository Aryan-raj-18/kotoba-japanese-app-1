# Kotoba Liquid Glass — Build 42 artifact correction

## User-reported issue

The JLPT Exam Q&A screenshot showed squared translucent panels behind the actual rounded question card. Similar rectangles appeared across the app on custom wallpapers.

## Root cause

Builds 39–41 accumulated overlapping CSS rules that applied `backdrop-filter` and translucent backgrounds to both **structural wrappers** (for example `.practice-stage`, `.stage-panel`, `.flash-mode`) and **actual visual cards** (`.exam-quiz-card`, `.flash-face`). The experimental SVG `feDisplacementMap` pseudo background also used an oversized filter region that could produce GPU compositor ghost plates.

## Correction

- Replaced the 753-line stacked glass stylesheet with one consolidated, documented single-surface stylesheet.
- Kept structural flex/grid wrappers transparent; `intro`/`results` panels with direct content are intentionally still styled as cards.
- Kept native rounded `backdrop-filter` on real visual surfaces, including header, footer navigation, page headings, practice cards, stories, writing, vocabulary, kana, map side panels, Settings, and dialogs.
- Removed runtime SVG filter/displacement-element injection; the MIT source attribution/license remains in the project but displacement is **disabled** due to repeated rendering artifacts. This trades the experimental prism edge-refraction for more reliable wallpaper-reactive frosted glass.
- Kept correct/wrong answer feedback, flashcard flip, Japan map SVG, large word grids, accessibility fallbacks, and the Liquid Glass switch intact.
- Updated asset build number and service worker cache from 41 to 42, so browsers can fetch the corrected stylesheet.
- Synced modified `app.py`, `templates/base.html`, `static/css/liquid-glass.css`, `static/js/liquid-glass.js`, and `static/sw.js` to the embedded Android source tree.

## Checks

- Python source checks: `test_glass_coverage.py`, `test_glass_integration.py`, `test_glass_surface_41.py` (updated for Build 42), `test_glass_artifacts_42.py` — all passed.
- JS tests: `node test_liquid_glass.cjs`, `node test_browser_cache.cjs` — passed.
- Actual Jinja2-rendered JLPT Exam Q&A HTML in Chromium: computed wrapper background transparent and `backdrop-filter: none` on both `practice-stage` and `exam-panel-quiz`; actual `exam-quiz-card` has `border-radius: 18px` with blur. Checked 1365, 390, and 320-pixel widths with no horizontal overflow.
- Full Flask regression tests, physical Android WebView, and Android APK build not run locally; verify in GitHub Actions/device before Play Store release.

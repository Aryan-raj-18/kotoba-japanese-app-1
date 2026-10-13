# Kotoba v1.0.0 — vocabulary categories and Liquid Glass coverage

## Category audit

Source data reviewed by automated validation:

- 408 core-kanji lesson records, including their vocabulary entries, and 15 supplemental kanji vocabulary entries
- 582 illustrated dictionary entries
- 1,999 frequency vocabulary entries
- 118 additional common everyday words
- 40 standalone everyday phrases
- 14 Roadmap sections containing 91 chapters
- 360 original Speaking & Shadowing sentences grouped into 24 situations

Across the four principal vocabulary feeds plus kanji vocabulary, **4,075 source entries** were scanned, representing **3,200 unique written terms** before Roadmap-only and other app-specific enrichment/deduplication. These are *source* totals, not a promise about how many cards appear in any one screen.

### Corrections

- Replaced substring categorization with whole-English-word matching, so `train` is no longer read as `rain`, `location` as `cat`, `stone` as `one`, `snow` as `now`, and `summer vacation` as `cat`.
- Added Japanese-word overrides where an English gloss is ambiguous: fish vs prepared fish dishes; fish market vs animal; goldfish vs food; train station vs weather; school vs general people; festivals vs weather.
- Corrected 30 unambiguous hand-tagged entries: 8 in the frequency dataset and 22 in the illustrated dictionary. Examples include `牛乳` → Food & Drink, `電気自動車` → Transportation, `稲妻` → Nature & Weather, `動物園` → Places & Buildings, and `アルバイト` → Work & Jobs.
- Prevented incorrect category emoji from using substring matches; e.g. a hot dog is 🌭 instead of 🐶 and train does not get a rain emoji.
- Kept animals, weather, holidays and seasons, transportation, food, people, and other categories in their respective topic groups without changing the underlying word texts, readings, quizzes, or speaking scripts.

### Verification added

`test_content_categories.py` now tests incorrect historical matches, correct animal/weather/season assignments, emoji identity, curated-dataset corrections, and basic Roadmap / speaking data completeness. It is added to the GitHub Actions validation workflow.

The category checks here validated 4,075 source vocabulary records and 15 high-risk classification examples; the test that imports Flask must still run in GitHub Actions. The study sets are large, and no automatic category classifier is guaranteed to make every context-dependent semantic distinction. Ambiguous words have been reviewed where identified.

## Liquid Glass audit and coverage

All ordinary page templates inherit `base.html`, which loads the Liquid Glass stylesheet and switch; the one landscape template is a partial used by another screen. Consequently, top-bar, bottom navigation and the Back button share the effect app-wide.

This update extends the *simulated, readable glass surface styling* across page-specific components: vocabulary lists, kanji and kana tiles, grammar cards, flashcards, quizzes, speaking panels, study progress, search results, games, JLPT, Roadmap, story/conversation cards, writing panels, informational/settings panels, and dialogs.

Only the persistent header/navigation and a few overlays use real backdrop blur. Large lists, quiz options and handwriting canvases deliberately avoid a live blur layer per element so Android/WebView performance, Japanese glyph contrast, correct/incorrect feedback, and accessibility remain reliable. Reduced-motion and reduced-transparency settings are respected, and users can turn off the extra finish in Settings.

Asset build is **36** (app version remains **1.0.0**), including the service-worker cache revision. The code and assets are also present in the Android package copy; GitHub Actions runs `sync_android.py` before building.

## Local verification

- Python syntax for both app sources and the new test: passed
- Static classification of source vocabulary + high-risk cases: passed
- Liquid Glass switch / Android CSS mirror / accessibility style smoke test: passed
- Service-worker cache version / offline routing smoke test: passed
- Speaking situation selector smoke test: passed
- Native `run_server` entry point: preserved in the Android app source

Not run locally: full Flask-based test suite and Gradle Android APK/lint jobs, because this environment does not have the Flask dependency; the complete workflow must still pass on GitHub Actions. Browser tests requiring `jsdom` likewise need the normal CI environment.

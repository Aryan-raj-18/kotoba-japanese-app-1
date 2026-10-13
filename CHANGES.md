# 1.0.0 — phone-width layout fixes (asset build 49)

Checked in a headless browser at 320 and 360 px. Not checked: a real Android device, other themes, dark mode, Liquid Glass OFF, tablet widths.

- Japan Explorer: the 680 px toolbar rule now comes after the 1100 px rule, so level buttons and the search box are no longer squeezed; filter chips never split a word. The Places count badge keeps its round shape.
- Japan lesson sheet and stamps panel are opaque; the prefecture name baked into the top-left of the 141 postcard SVGs is removed (also in build_japan_explorer.py), so the overlay pills no longer collide with it.
- Home: the hero title is no longer capped at 12ch, so it wraps to two lines.
- Padding added to text in bordered boxes: grammar examples, the Home "Saved on this device" strip, "View stamps & region progress", the Writing hint, the plain `.btn` class (/sync) and the back links.
- Grammar detail headings have space above them.
- Writing mode buttons stay on one line.
- Footer lines up with the 8 px page margin and its last line is no longer hidden behind the bottom nav.
- Search button on Home and Search is excluded from the glass button style (it was cream on cream).
- app.py removes spaces between Japanese characters in `example_ja` for grammar and frequency words when the data loads; the JSON files are unchanged. Search cache regenerated.
- ASSET_BUILD and the service-worker cache name moved to 49 (sw.js precache still said ?v=47, which test_responsive_shell caught). Version code is unchanged.

# 1.0.0 — Liquid Glass and text layout (source build 47)

- Unified glass surfaces across pages, controls, dialogs, header, bottom navigation, the original logo frame and native opening screen.
- Retained the saved global Liquid Glass switch, with solid OFF surfaces, keyboard controls and lightweight fallbacks.
- Reflowed kanji details, reading boxes, vocabulary, grammar, radicals, roadmap, Japan Explorer and practice layouts to contain full text at narrow widths.
- Preserved primary-action contrast, selected/correct/incorrect answers and existing content/fonts/logo files.
- Fixed Japan city-list rows shrinking during the tap ripple, which could prevent a lesson opening.
- Synchronized Android sources and caches; public version 1.0.0, version code 47. New APK/AAB compilation and physical Android QA are pending.

Historical changes follow.

# 1.0.0 — first public release, content restored (build 20)

- Restored the complete prior learning datasets: N4–N1 and N5 kanji, quizzes, exam Q&A, timed practice, grammar, vocabulary, stories, dialogues, radicals and all roadmap lessons.
- Removed the starter-only generator so future builds cannot silently replace the restored course with previews.
- Replaced 177 earlier phrasebook-derived Speaking & Shadowing cards with 360 independently written sentences across 24 everyday situations (120 Easy, 168 Medium, 72 Hard). Added a situation filter to the existing practice-set/difficulty selectors; listening, speech recognition, recording and self-check are unchanged.
- Preserved all current search, startup, map, speaking, backup, Android session and privacy fixes.
- Public version remains 1.0.0; internal build number is 20 and signing identity is unchanged.
- Updated content source notices to describe the restored reference-derived material accurately.

## Liquid glass finish (asset build 35)
- Added theme-aware frosted header, floating bottom navigation, premium answer panels and subtle water-glint progress, without touching learning data.
- Added Settings toggle, reduced-motion/transparency and low-memory fallbacks, Android asset sync, and matching tests. App version remains 1.0.0.

- Build 38: made Liquid Glass more background-reactive so header, footer, settings, and major cards pick up more color from wallpapers/themes while preserving readability.

- Build 39: adapted upstream MIT Liquid Glass refraction for Flask/Android, removed unused decorative themes while retaining accessible Light/Dark/Auto and wallpapers.

- Build 42: fixed recurring rectangular Liquid Glass ghosts by styling visible panels only (not layout wrappers), disabling unsafe SVG displacement, retaining wallpaper blur, and updating offline assets.

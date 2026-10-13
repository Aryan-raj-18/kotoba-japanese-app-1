# Kotoba 1.0.0

Offline Android Japanese study app built by Aryan Raj. Flask runs inside Android via Chaquopy 17; the WebView displays local pages. Public version 1.0.0, internal Android build 30.

The full course content has been restored: 1,991 JLPT kanji (N5 103, N4 174, N3 393, N2 410, N1 911), 2,103 kanji catalog entries, 229 grammar entries, 1,999 ranked vocabulary entries, 582 picture-dictionary entries, 19 restored stories and 50 restored dialogues, plus the four recent original stories and four recent original dialogues and practice questions for all five levels. All 91 roadmap chapters are accessible. CONTENT_RESTORATION.json records every restored dataset. Level tags are approximate study guidance rather than an official exhaustive JLPT syllabus.

The search, startup, map gesture, speaking-score, atomic backup, privacy and Android session fixes remain. Generated word-learning examples retain the safe literal example builder; it avoids guessing contextual readings and meanings. Signup and login are removed. Existing local study data is preserved; older records can be selected in Data controls without a password. Backup & Restore transfers study data without passwords or automatic cloud synchronization.

Build with Python 3.13, JDK 17, Gradle 8.13, Android API/build tools 36. Install requirements.txt and run python sync_android.py, then build in android/. Signed releases need the private upload signing kit; read RELEASE_CHECKLIST.md. Never commit signing material or runtime user data.

Verify with test_restored_content.py, test_release_safety.py, test_search.py --android, smoke_test_android.py, test_voice_search.js and the two jsdom tests. VERIFICATION.json records automated checks and remaining device QA. CONTENT_LICENCES.md explains attribution and restored reference-derived content; the publisher must verify distribution permissions before publishing.

Real-device and Play internal-track testing remain required before production. privacy-policy.html is ready to host; /privacy and /data-controls are available in the app.

Timed JLPT mock exams clearly highlight the selected option and show a Selected marker. Every option remains selectable until submission or time expiry; choices can be changed and are preserved across question navigation. Run `node test_jlpt_mock.cjs` with jsdom installed to check this flow.

Build 23 repairs learning Back navigation, uses each theme's card palette in grammar/practice/letter boxes, and uses on-yomi for standalone numeral questions and cards. Counter words, dates and compound numbers retain their contextual readings; original course JSON is unchanged and alternate readings remain searchable.

The Japan place sheet, passport, expanded map and other dialogs now share a background scroll lock. Nested panels retain the lock, and closing the last panel restores the underlying page position.

Android startup reuses a live process-wide lesson server, keeps bind failures retryable, identifies the app's own health response, cleans up destroyed WebViews and offers Retry after a bounded 30-second wait. Saved study data stays in place. Native cold/warm launch and touch behavior still need actual-device testing; the reported phone freeze was not reproduced on a connected device.

New regression suites: test_navigation_theme.cjs, test_scroll_lock.cjs and test_numbers_startup.py. The tests use simulated DOM behavior and desktop Python; they do not claim Android lifecycle or gesture physics verification.

Build 24 preserves kanji list level/search and position when returning from a detail, including the N4 list. The Android display container now reserves system-bar/cutout space before the WebView; Settings provides a saved Hide status bar switch, with native immersive handling restored on resume and window focus.

The theme picker includes seven original skins: Anime Dawn, Neon Tokyo, Kyoto Paper, Bamboo Zen, Matsuri Lantern, Fuji Mist and Water Glass. Each changes semantic colors, original SVG app icons, Japanese/Latin type combinations and a brief title/icon reveal. Full Japanese fonts are bundled for offline use with their SIL OFL notices. Follow device appearance remains a separate switch. Older saved theme choices migrate to corresponding new skins, and user wallpapers remain available. System reduced-motion settings suppress skin-switch animations.

Run test_kanji_themes.cjs for the kanji-return, theme migration, icon/type/motion, color contrast and native display-bridge interaction checks. These tests simulate the DOM/native bridge; Android status-bar gestures, physical touch and actual font layout remain real-device QA tasks.


Build 25 makes online/offline behavior explicit on Home, Settings → Internet & cloud sync and startup. Progress saves locally in either mode. Optional Firebase cloud sync, durable retries, conflict controls, private device-connection keys and cloud deletion are implemented. The shipped backend configuration is disabled until the publisher provides and deploys its project; see CLOUD_SETUP.md. No live cloud success is claimed.

Audio playback and capture now interrupt each other. Back, closing a speaking popup, leaving a page and app backgrounding stop speech; stale capture results cannot award progress. Android stops TTS before opening the microphone and guards a brief buffer-clear delay.

The six themes retain their palettes/icons/motion and add bundled variable Nunito Sans / Space Grotesk UI fonts, original static Japanese SVG motifs, clearer type spacing and letter previews. No remote font downloads or continuous background effects are added. Physical font/audio/lifecycle testing remains required.

## Fixed Kotoba identity and Water Glass — build 26
The header and opening screen use the existing app icon and fixed brand lettering across all seven themes. Water Glass is an additional aqua skin with static ripple artwork, frosted panels, an offline Mincho/geometric font pairing and a brief reduced-motion-aware reveal. Solid surface fallbacks and a reduced-transparency preference keep the finish readable. Existing wallpapers, content, audio controls and offline/local saving remain available.

The native host now loads a bundled self-contained copy of the intro while Python initializes, replacing the extra Opening your lessons page. Elapsed/skip state continues into the web intro, so it does not run twice or add another three seconds. A 30-second failure/retry path remains. `sync_android.py` rebuilds the native opening asset from the shared template/styles/icon and offline brand font.

## Section rendering, classic fonts and logo — build 27
Kanji and Everyday render 96 entries per batch; compact metadata keeps the full catalogs searchable, and Show more appends further entries. Kanji Back restores level, query, loaded range, selected entry and scroll. Global-search word links open the exact entry even outside the first batch. Public versioned assets are cached and page scripts load in parallel using defer; pages and learner APIs stay uncached. Android uses its bundled assets directly and retires redundant service workers, while browser offline caching remains available. Repeated per-card backdrop blurs are removed; glass chrome remains.

The earlier Source Serif 4 / Japanese Mincho font style is restored for every theme, bundled offline. The same existing app icon and fixed navy/cream logo presentation are used throughout the header and opening screen. Themes retain their palettes, background motifs and semantic icons, including Water Glass. Phone rendering/startup/performance checks remain pending.

## Sakura Journey design — build 28

See DESIGN_UPDATE.md for the implemented dashboard, landscapes and featured themes. Existing palettes remain available under More palettes. Daily goal opens Settings directly; a browser check and test_journey_home.cjs cover click propagation and focus. All course JSON remains unchanged. Current automated, browser and package verification is in VERIFICATION.json.

## First-launch setup — build 29

The five starting-point choices appear only on their first actual display. The existing onboarding preference is retained so previously completed setup does not repeat after an upgrade. Placement, leaving before selecting, skip and dismissal all leave setup recorded. The upper app header is hidden only while the setup panel is open and returns afterward. All themes, lessons and prior fixes are retained.

## Kanji notification — build 30

Settings → Kanji notification & lock screen, or Show this kanji in a notification on a kanji detail. Choose N5–N1 or a selected subset. Rotation supports 15–1440 minutes per card; one-card display supports 1–1440 minutes; Keep until I stop has no timer. Show/hide meanings and readings. The native offline notification offers Next and Stop and opens the exact kanji when tapped. Settings survive reopening and alarms are restored after reboot/upgrade. Notifications are off by default and require user permission.

The notification shade and lock screen can show full text. The kanji is also a monochrome notification icon for compatible always-on displays; full text and placement on AOD are controlled by the phone. Android can defer background rotation. No overlay, exact-alarm, foreground-service or battery-exemption permission is added. Real-device behavior remains to be checked.

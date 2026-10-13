# Kotoba 1.0.0 — Play release handoff

Package `com.kotoba.app` · version 1.0.0 · version code 33 · min API 24 · target API 36 · arm64-v8a and x86_64.

The public version is 1.0.0. Internal build number 33 follows the earlier development builds and the version-renaming build; increase it for future uploads.


## Public privacy policy — 10 October 2026

The Play Console privacy-policy URL is: https://kotoba-privacy-policy.swiftlamb64.chatgpt.site

The Sites page is published with public access. It contains the current app policy, including publisher/contact details, local/offline study data, optional Firebase sync and private cloud keys, microphone/system speech, files/backups, notifications, retention/deletion and feedback. The standalone HTML copy now matches the current in-app policy text. Public contact: Aryanrajr868@gmail.com. Native app code and signed build 33 APK/AAB are unchanged by this hosting task; the in-app Privacy page is already accessible through the app menu and footer.

Paste the HTTPS URL into the Privacy policy URL field and save the Play Console form. Do not paste a local file path or upload the HTML file as the URL. Data safety, audience declarations, physical-device checks and Play internal/pre-launch testing remain separate release tasks. If the publisher activates Firebase or changes data handling, update both policy copies and the Data safety declaration before publishing that changed build.

## Latest update — build 33, 10 October 2026

- Opening Smartphones & Apps or another word-card chapter from Home's Next on your journey now remembers Home as the source. Header Back, native first-card Back, completed-lesson Back and a confirmed practice exit return to the Home preview at its saved scroll position. Browser Back and delayed font/fragment layout also preserve the position. Continue learning uses the same source marker for roadmap lessons.
- Next lesson carries the Home source into the following chapter. Opening a lesson from the full roadmap still returns to that same chapter and exact roadmap scroll position. Previous-word Back remains within the current lesson. Return destinations are fixed internal URLs; unrecognized origin values fall back to the roadmap.
- Roadmap fragment targets no longer extend sideways: only their compact children form the zigzag path, with smaller offsets on narrow screens. Programmatic chapter/recommendation scrolling changes only the vertical position and resets horizontal scroll. This prevents the Modern Life banner and other section headings from shifting off the left edge.
- No chapters, learning content or features were removed. All 91 open chapters remain; all 21 public learning JSON files are byte-identical to build 32. Public version stays 1.0.0; internal version code is 33.

360 automated regression checks passed: 350 Python/DOM and 10 native Kotlin model checks. The compiled signed AAB passed 6,974 GET requests plus POST, backup and repeated-server checks. Nine current Chromium scenarios cover Sakura Journey, Kyoto Night and Water Glass at 320, 390 and 1180 pixels: exact Home/roadmap return positions, previous-word Back, native Back entry point, header and browser Back, confirmed quiz exit, actual quiz completion, next-lesson source, every zigzag offset and enlarged-text horizontal fit. Signed APK/AAB, original upload certificate, bundle validation, compiled/source asset equality, identical APK/AAB Python/Dex payloads and 16 KB package/native alignment passed. Release lint: 0 errors, 33 warnings.

Before production, install this signed update over the existing app to preserve data, then repeat Home → Smartphones & Apps → word cards → Back and full roadmap → chapter → Back on the actual phone. Physical Android WebView/Back, upgrade, offline cold/warm launch, actual TTS/microphone, notification/AOD and Play internal-track/pre-launch testing remain pending. Previous build 32 test results are archived; they are not presented as current build 33 browser results.

## Latest update — build 31, 10 October 2026

- Notification kanji selection now uses individual themed checkboxes. Tapping, deselecting, changing preview controls, applying, receiving a native reply and clearing selection no longer rebuild the list. Selected cards survive filtering. The list scrolls independently and keeps its current region.
- Header, home and Search offer offline suggestions as you type: for example sor → 空 / そら / sora. Every result opens that exact dictionary entry and its own meaning. Japanese, English and romaji prefixes are supported; full-word/sentence matching remains precise. Input is debounced, stale responses discarded, Japanese IME composition respected, keyboard navigation supported, and the popup can open above the input to fit around bottom navigation/keyboard space. Submitted incomplete queries also show suggested entries.
- All 91 roadmap chapters remain accessible and retain their IDs, vocabulary, examples and questions. Kana/greetings/numbers lead into basic particles and sentences; N5 everyday topics and its kanji checkpoint precede N4 vocabulary, longer sentences and reading/conversation, then N3, N2, N1 and the final mixed review. Existing completion/start preferences remain valid. The grammar review still includes all its former topics across the two grammar stages. Stage links and accurate N5–N1 descriptions replace the old intermediate-only description.
- Lock-screen help explains how to enable full kanji notification cards and offers channel/phone settings shortcuts. Android determines placement relative to the clock/weather and AOD text/icon display; Kotoba cannot pin a card below the weather. This update does not override the system lock screen.
- The packaged search cache now supports compiled Android modules, validates the build and public content, and includes a prepared prefix index. The actual compiled bundle loaded it before the first query. Recorded desktop prefix timings are in verification/prefix-timing-compiled.json; these are not device timing guarantees.

302 regression checks passed: 292 Python/DOM and 10 native Kotlin model tests. The final compiled AAB passed 6,974 GET requests, plus POST, backup and repeated-server checks. Desktop Chromium passed 45 main layouts plus six enlarged-text layouts (51 total) across Sakura Journey, Kyoto Night and Water Glass. Notification settings used a simulated native bridge. Signed APK/AAB, preserved certificate, bundle validation, source/payload equality and 16 KB package/native alignment passed. Release lint: 0 errors, 33 warnings, including inherited warnings and optional KTX syntax suggestions. Twenty public learning JSON files are byte-identical to build 30; roadmap restructuring preserves every chapter’s lesson content and is recorded in CONTENT_RESTORATION.json.

Before production, test on the actual Android device: upgrade without losing progress, scroll and select several distant kanji, search with Japanese/romaji and the keyboard, follow stages and reviews, cold/warm opening, and permission/lock-screen/AOD behavior. Actual lock-screen placement cannot be verified in desktop Chromium. Physical Android and Play internal-track/pre-launch testing and the publisher production tasks below remain pending. Public version stays 1.0.0; internal version code is 31.


## Latest update — build 32, 10 October 2026

- Speech follows each card's own displayed kana. For example mei → めい, a kun-yomi card uses that kun-yomi, and an on-yomi card uses that on-yomi. No dictionary-wide replacement changes contextual word readings. This covers roadmap, vocabulary, verbs, search/examples, flashcards/review, speaking/shadowing, stories/dialogues and Japan Explorer. Where the source has no kana reading, the original Japanese text remains the speech fallback.
- Kanji pages and JLPT popups expose labeled on/kun audio choices. Their main button names its study reading. Isolated numeral study still uses on-yomi, while counters, dates and compounds retain their recorded contextual readings.
- Flashcards carry a dedicated full reading rather than spoken romaji/metadata or truncated notes. Review records retain it. Exam feedback and timed-test review read available furigana segments. Grammar pattern and example audio remain available as separate controls.
- Corrected a confirmed transcription error in the display copies for 名: kun-yomi な, on-yomi メイ/ミョウ. Verified against [Kanjipedia](https://www.kanjipedia.jp/kanji/0006666900) and the app's JLPT dataset. The original source snapshots are preserved. Existing saved favorites/reviews with that exact erroneous reading are repaired on display without deleting their progress; legacy isolated-number readings also follow the on-yomi policy.
- Roadmap remembers the selected chapter and scroll position. In-app Back, browser Back, completed-lesson Back and a confirmed practice exit return to that part of the path. Late fragment/font layout no longer overrides it. All 91 chapters and all 21 public learning JSON files are unchanged from build 31.

349 automated regression checks passed: 339 Python/DOM and 10 native Kotlin model tests. The final compiled AAB passed 6,974 GET requests, plus POST, backup and repeated-server checks. Desktop Chromium passed nine current speech/roadmap scenarios across Sakura Journey, Kyoto Night and Water Glass at 320, 390 and 1180 pixels. These verified exact scroll restoration, browser Back, displayed kana sent to a simulated native speech bridge, on/kun selection and horizontal fit. Previous build 31 browser/timing checks are archived and are not counted as current browser checks. Signed APK/AAB, preserved upload certificate, bundle validation, all compiled/source assets, identical APK/AAB Python and Dex payloads and 16 KB package/native alignment passed. Release lint: 0 errors, 33 warnings.

Physical Android audio and WebView testing, upgrade without data loss, cold/warm offline launch, microphone coordination, lock-screen/AOD checks and Play internal-track/pre-launch testing remain pending. Check pronunciation using the phone's actual Japanese TTS voice. Public version remains 1.0.0; internal version code is 32. Install this signed update over the existing app to preserve device data.

## Files and signing

Upload the signed `kotoba-1.0.0-release.aab` to **Play Console → Testing → Internal testing** first. An AAB is a publishing file, not a phone installer. The release testing APK can be installed directly for initial checks.

The separate **private signing kit** contains the new upload keystore, its password properties and public certificate. Keep it private and backed up. Never upload the kit to a public repository or attach it to a public issue. Copy the keystore and `upload-signing.properties` into the `android/` folder only when building signed releases. The source ZIP deliberately excludes signing material and runtime user data.

This kit is suitable for a **first Play release** with Google Play App Signing. If this package already exists in your Play Console, use its existing accepted upload key or the Console’s upload-key-reset process. A new key cannot silently replace an existing certificate. Future builds must use the same upload key and an increased version code.

The Play-installed app can have a different app-signing certificate from a sideloaded APK. Do not uninstall a current build until you have exported a backup. If Android reports a signature mismatch, preserve/export data from the existing installation before moving to the Play build. Import the backup after installing the new build. Signup and login are removed. Progress stays on the device; Backup & Restore transfers it to another device. Older saved study records can be selected in Data controls without a password.

## Required before a production rollout

1. Install from the Play internal track on at least one real ARM64 device. Run the Play pre-launch report and resolve any reported crashes/ANRs.
2. Measure cold and warm launches. Check the retained three-second intro, Japanese font rendering, map zoom/pinch/pan, edge-to-edge layouts, Android back gestures, and app resume/recreation. Desktop timings and DOM tests do not establish a device frame rate or startup-time guarantee.
3. Verify Japanese TTS with and without an installed Japanese voice, recognition with microphone denied/allowed, offline fallback, notifications denied/allowed, and reminder delivery after reboot. Speech recognition availability depends on the installed system provider.
4. Export a backup using the Android document picker, cancel a save, import a valid backup, reject an invalid backup, reset progress, select/delete one previous study record, and confirm the other records and device data remain intact. Test upgrade/migration from the actual installed old APK, because its signing key may differ from earlier development builds.
5. Test on a 16 KB page-size Android emulator/device. The delivered native ELF alignment and APK ZIP alignment were inspected, but that is not a runtime 16 KB device test.
6. Enter **https://kotoba-privacy-policy.swiftlamb64.chatgpt.site** in the Play Console Privacy policy URL field. The public HTTPS page is published with public access, and its text matches the current app-internal `/privacy` page. `privacy-policy.html` is the standalone copy. The downloaded HTML file is not the URL to paste into Play Console.
7. Complete store listing, real device screenshots, feature graphic, support email, content rating, target audience, app access (no login or special credentials required) and Data safety. The app contains no ads/analytics and its study data remains local. **Do not automatically declare “no data collected”:** optional system speech recognition may process audio off device; assess that actual flow against Play’s current Data safety rules. Declare any emailed feedback/contact data and optional voice flow accurately. Permissions are requested for optional microphone and notifications; photo/backup access uses system pickers.
8. Verify the developer contact (`Aryanrajr868@gmail.com`), audience declaration and privacy wording match the publisher’s actual practices. The full previous learning material has been restored. Verify distribution permissions for reference-derived learning text and questions, preserve source attribution, and describe the actual N5–N1 study coverage without claiming an official or exhaustive JLPT syllabus.

For personal developer accounts created after 13 November 2023, Google currently requires a closed test with at least 12 testers opted in continuously for 14 days before applying for production access. Follow the requirements shown in your Console. Google controls production approval and account-specific testing eligibility. No production submission or rollout has been performed by this handoff.

## Local build and checks

Use Python 3.13, JDK 17, Gradle 8.13, Android platform 36 and build tools 36.0.0. Install `requirements.txt`, then:

```sh
python sync_android.py
python test_restored_content.py
python test_release_safety.py
python test_search.py --android
python smoke_test_android.py
node test_voice_search.js
node test_navigation_theme.cjs
node test_kanji_themes.cjs
node test_journey_home.cjs
node test_intro_startup.cjs
node test_catalog_batches.cjs
python test_asset_loading.py
node test_audio_lifecycle.cjs
node test_cloud_sync.cjs
python test_cloud_sync.py
node test_scroll_lock.cjs
node test_jlpt_mock.cjs
python test_numbers_startup.py
# jsdom@26.1.0 is required by test_japan_map.cjs and test_speaking.cjs.
cd android
gradle :app:assembleRelease :app:bundleRelease :app:lintRelease
```

`KOTOBA_BUILD_PYTHON` can point to the Python 3.13 executable. Android runtime learner data is stored under the app’s private `files/learner-data` folder, rather than in replaceable package assets. Legacy data is copied before Python starts. The generated search cache contains only public learning content and is invalidated by changes to its source data/code.

`VERIFICATION.json` records completed automated checks and remaining device-only checks. `CONTENT_LICENCES.md` describes the learning content and map provenance. No claim of “zero bugs” or guaranteed 60 FPS is made.


## Release review — 9 October 2026

The no-login build retains all N5–N1 content and features. Old `/login`, `/signup` and `/logout` routes are absent; no password can be entered or a new account created. Current old study records survive cookie expiry through a device marker; other older records remain available in Data controls. Fresh installations use device study data. Native app-session authorization and destructive-action confirmation/CSRF remain enabled.

Current Google documentation was reviewed:

- Target API requirements: https://support.google.com/googleplay/android-developer/answer/11926878 — new mobile apps/updates require API 36 from 31 August 2026. This build targets API 36.
- Native memory compatibility: https://developer.android.com/guide/practices/page-sizes — ELF/ZIP alignment is checked locally; a 16 KB Android runtime test is still required.
- Privacy/Data safety: https://support.google.com/googleplay/android-developer/answer/10144311 — a public, active policy URL and accurate declarations are required. The public policy is now published at https://kotoba-privacy-policy.swiftlamb64.chatgpt.site. Play Console forms remain to be completed by the publisher.
- Account-specific testing: https://support.google.com/googleplay/android-developer/answer/14151465 — see the closed-test requirement above.

No Android device was connected to this workspace and no accelerated emulator was available. Automated route, content, search, security/data-preservation and JavaScript interaction checks are completed here; physical-device/native lifecycle, permission, document-picker and reminder tests remain in the list above. This is an internal-testing release candidate, not a production-approval certificate.


## Previous automated checks for build 21

- 6,969 packaged page/API requests, including all learning IDs and all five JLPT levels, passed using the compiled Python content extracted from the final signed AAB.
- 16 search, 15 release/data-safety, 5 full-content, 8 voice-search, 20 map-interaction and 2 speaking checks passed. Every restored dataset hash remains unchanged.
- Signed release APK and AAB built successfully; Android release lint: 0 errors, 21 warnings. Warnings include intentional JavaScript-enabled WebView use and cosmetic/icon/Kotlin suggestions; they remain documented in verification/lint-results-release.txt.
- AAB bundletool validation, upload-certificate preservation, APK signature verification, APK 16 KB ZIP alignment, native ELF alignment and bundle PAGE_ALIGNMENT_16K checks passed.
- The final AAB contains no login/signup templates or installation-specific learner data. All packaged Python sources and public assets match the final staged app.

Remaining production tasks are listed above. No connected-device test or Play Console submission was performed.


## Timed JLPT mock selection fix — build 22

Selected answers have a themed highlight, a visible Selected marker and an accessible pressed state. Learners can pick any option and change their answer before submitting or time expiry. The selection survives Previous/Next, question-palette and flagged-question navigation. Selecting an answer preserves keyboard focus and does not reveal correctness. Submission uses the latest choice and duplicate submit/timeout events cannot record a result twice. No learning content or other feature was removed.

The new DOM interaction suite covers all five levels, all options, navigation, changing answers, grading the latest choices, duplicate submission and timeout. Device presentation still needs the real-device checks above.

Completed build 22 checks: 8 timed-mock interaction checks against the final AAB assets, 6,969 page/API requests using compiled modules extracted from that AAB, and 5 course-preservation tests. The signed APK/AAB built successfully; lint reports 0 errors and 22 warnings. Signatures, preserved upload certificate, official bundle validation, native ELF and APK 16 KB alignment, and equality of all packaged sources/assets passed. Earlier unrelated interaction/search/safety checks are recorded as build 21 evidence in VERIFICATION.json.

## Navigation, themes, number readings and startup — build 23

This update retains all lessons, map zoom, the intro and timed-mock selection. Signup and login remain absent. The original course JSON datasets are byte-for-byte unchanged.

- Back closes the current popup first, uses the actual Previous control where available, and asks before ending an unfinished round. Completed rounds return to that section's setup. Directly opened roadmap chapters return to Roadmap. Expanded maps close before page navigation.
- Grammar, kana, answer boxes, tracing and learning cards use the active theme's card and text tokens. Undefined color/font aliases that caused bright fallbacks have been replaced. Selected mock answers retain their highlight.
- Standalone numeral questions, vocabulary copies, kanji flashcards, placement and search displays use on-yomi. Valid kun readings remain in reference data and search aliases. Counter words, dates and compound numbers retain correct contextual readings: 一つ remains ひとつ and 四十 remains よんじゅう. No automated global text replacement was applied to Japanese sentences.
- Japan place details, the passport, expanded maps, settings and learning popups now freeze the hidden underlying page while allowing their own content to scroll. Nested overlays share the lock; closing the last overlay restores the map/page position. The lock resumes after browser page-cache restoration.
- Android reuses a live lesson-server worker across Activity recreation. Failed server binds no longer leave a false running flag. The startup probe checks that the responding server identifies itself as Kotoba, and a separate 30-second UI deadline offers Retry instead of an endless loading screen. Destroyed WebViews are cleaned up. Retry preserves device study data.

The exact phone freeze has not been reproduced on a connected Android device. Server failure/retry and fresh native-session authorization are tested in Python; DOM checks validate overlay/navigation state, not physical touch scrolling. Before release, install this build **over the current same-signature installation**, export a backup, then test:

1. Open a Japan place after scrolling the explorer page. Swipe its content to both ends repeatedly; the underlying map/page must stay still. Close it using ×, backdrop and Android Back; its original scroll position and zoom must remain.
2. Open settings over place details, close only settings, and verify the background stays locked. Open a place from the passport, close it, and repeat in the expanded map. Verify ordinary page scrolling works once all panels are closed, including after rotation/backgrounding.
3. Test Previous and Android Back during practice learning, quizzes, timed mocks, review, speaking and roadmap lessons. Keep practicing must preserve the current round; leaving must return to its own setup. Mock answers must remain selected when revisiting questions.
4. Check all six current themes with/without wallpaper in grammar, tracing, kana, quizzes and the dashboard. Large text and a small phone screen must not clip options or hide close controls.
5. Launch/close/reopen at least ten times, then repeat after Home/backgrounding, force-stop and relaunch, reminder launch and Activity recreation. Saved study progress, theme and wallpaper must remain. If loading fails, verify Retry appears and capture the Android Logcat error; an endless wait is not acceptable.

## Earlier appearance suggestions — build 23 (theme choices superseded below)

These are suggested future polish items, not features removed or a redesign already applied:

| Area | Suggestion | Purpose |
| --- | --- | --- |
| Everyday light theme | Keep Washi: warm ivory cards, indigo actions and restrained red accents | Matches the Japanese paper identity and gives lessons a calm reading surface |
| Everyday dark theme | Keep Sumi: charcoal background, opaque dark cards and clear selection contrast | Comfortable dark presentation with readable Japanese text |
| Optional character | Keep Sakura and Yozakura as soft blossom/night alternatives; Matcha remains available | Gives variety without changing navigation or study content |
| Panel motion | Consistent 180–250 ms opacity/transform transitions; no background parallax while learning | Makes opening/closing feel coherent and avoids distracting movement |
| Progress and rewards | A brief progress-bar fill and small one-time achievement/answer animation | Emphasizes learning events without constant motion |
| Performance | Limit expensive glass blur to a few surfaces; profile on a lower-end Android phone | Helps decide where visual effects should be simplified based on measured frame times |
| Accessibility | A manual Reduce motion choice alongside existing system reduced-motion support | Gives learners control over animation intensity |
| Visual consistency | A single icon style and spacing scale across dashboard cards and section buttons | Makes the app feel more cohesive |

Keep the next release focused on reliable launch, gestures and study correctness. Additional effects should not lengthen the three-second intro or delay access to lessons. No measured native frame-rate claim is made.


## Kanji return, system bars and six new skins — build 24

Kanji details opened from the N4 list return to N4, retaining search and scroll position. The same behavior covers the other level filters. Direct-open detail links carry a validated local return path; external URLs and invalid levels cannot become a return destination.

The Android status icons were overlapping the header in the supplied screenshot. Insets are now handled by a native parent container and zeroed for the WebView to avoid duplicate padding. The **Hide status bar** switch in Settings saves its choice in Android preferences and applies it on launch, resume and window focus. Swipe from the top to temporarily reveal hidden system bars. The gesture/navigation area and physical cutout remain protected. This is a native implementation change, not a connected-phone verification.

Current theme options replace the previous five palettes:

| Theme | Look | Lettering and motion |
| --- | --- | --- |
| Anime Dawn | Pastel sky and pink, star-framed icons | Rounded Japanese; spring reveal |
| Neon Tokyo | Deep navy, cyan and magenta, angular icons | Crisp Japanese with monospace UI; electric reveal |
| Kyoto Paper | Ivory and vermilion, torii-framed icons | Mincho; ink fade |
| Bamboo Zen | Sage and forest green, bamboo accents | Rounded Japanese and clean UI; quiet rise |
| Matsuri Lantern | Burgundy and lantern gold | Mincho headings and rounded UI; festival pop |
| Fuji Mist | Ice blue and slate, mountain accents | Mincho headings and clean UI; soft mist reveal |

Theme changes update in-app navigation, header and home-focus icons without changing controls, study characters or meanings. Six type combinations and six short motion presets are coordinated with the palette. Bundled Rounded Mplus 1c and Shippori Mincho fonts work offline; attribution/licences are in static/fonts/. Follow device appearance automatically chooses Anime Dawn or Neon Tokyo. Old saved themes migrate to corresponding new skins; wallpaper uploads and saved framing are preserved. System Reduce motion is respected. The app launcher icon is unchanged.

Before release on a phone, check: N4 → detail → Android Back and both visible return controls; returning after a search; all six themes on grammar/kana/tracing/quizzes and settings; theme persistence after reopening; Hide status bar both on and off after Home, keyboard use, rotation, file picker and notification launch; status and navigation icons on light/dark skins, cutouts and three-button/gesture navigation; large-text layouts and whether every setting remains reachable. Native system-bar behavior and actual font layouts cannot be certified by DOM checks.

Implementation follows official Android guidance:
- https://developer.android.com/develop/ui/views/layout/immersive
- https://developer.android.com/develop/ui/views/layout/webapps/understand-window-insets


Completed build 24 checks: 6,969 GET route requests plus POST, backup and repeated-server smoke checks using compiled modules extracted from the final signed AAB; 13 number/server, 16 search and 15 safety regressions; 22 kanji-return/theme/display, 27 navigation/theme, 14 overlay-scroll and 8 timed-mock DOM checks against final AAB assets; 5 content, 8 voice-search, 20 map and 2 speaking checks. These total 150 regression/interaction checks in addition to the route smoke audit. All passed.

The clean signed APK/AAB build passed with lint 0 errors and 26 warnings. Bundle validation, both artifact signatures and the preserved upload certificate, native ELF alignment (134 libraries per artifact), APK 16 KB ZIP alignment, PAGE_ALIGNMENT_16K and equality of all packaged Python/public assets passed. The APK and AAB contain identical application payloads. Verification records and checksums are included in the source ZIP. This is an internal-testing candidate; the real-phone checks above and Play Console production tasks remain outstanding.


## Online/offline saving, cloud preparation, audio and theme polish — build 25

The app explicitly explains that it opens and saves local progress with or without internet. The local startup health probe bypasses external proxies. Startup remains bounded by Retry; this does not establish the cause of the screenshot's preparing screen on a connected phone.

Automatic Firebase cloud sync is implemented with durable snapshots, bounded request timeouts, identity refresh, conditional writes, validated downloads, explicit conflict resolution, private cloud connection files for users' own devices and queued cloud deletion. **The delivered configuration is disabled and no live project is connected.** CLOUD_SETUP.md defines the publisher configuration, security rules, privacy/Data safety updates and live acceptance tests needed before activation. No login/signup screen was added. File backups remain available in both modes.

Speech only begins from a playback action. Starting a mic stops TTS and recording playback; Listen cancels active recognition. Android gives the speaker a short buffer-clear interval before capture. Section changes, popup close, Back, page leave and app backgrounding stop speech. Page/capture tokens protect against delayed recognition and permission callbacks. Actual acoustic tails, microphone permissions and native lifecycle behavior still need phone testing.

Theme polish retains all six skins and palettes, adds offline variable UI fonts with OFL notices, static original Japanese background motifs and letter previews, and keeps uploaded wallpapers and reduced-motion behavior. There is no continuous background animation.

Additional phone checks: Listen → immediately Mic → Listen repeatedly; voice search while a story or conversation plays; close a kana/word popup while speaking; Back/Next, Home/background, permissions and reopening; all six fonts with large text and wallpaper on a small screen. Airplane-mode/online save-restart-backup checks and live cloud pairing/conflict/deletion checks are in CLOUD_SETUP.md.


Completed build 25 checks: 6,971 GET route requests plus POST, backup and repeated-server smoke checks using compiled modules extracted from the final signed AAB; 13 number/server, 16 search and 15 safety regressions; 22 kanji-return/theme/display, 27 navigation/theme, 14 overlay-scroll and 8 timed-mock DOM checks against final AAB assets; 5 content, 8 voice-search, 20 map and 2 speaking checks. 28 cloud/offline regressions against a simulated provider, 11 cloud/offline DOM checks and 13 audio lifecycle DOM checks also passed. These total 202 regression/interaction checks in addition to the route smoke audit. All passed.

The clean signed APK/AAB build passed with lint 0 errors and 26 warnings. Bundle validation, both artifact signatures and the preserved upload certificate, native ELF alignment (134 libraries per artifact), APK 16 KB ZIP alignment, PAGE_ALIGNMENT_16K and equality of all packaged Python/public assets passed. Cloud service configuration remains disabled; no live Firebase or physical-phone test is claimed. The APK and AAB contain identical application payloads. Verification records and checksums are included in the source ZIP. This is an internal-testing candidate; the real-phone checks above and Play Console production tasks remain outstanding.


## Fixed brand identity and Water Glass — build 26

The existing Kotoba app icon and fixed brand fonts/colors now remain consistent in the header and opening screen across all seven themes. Water Glass adds aqua tones, static water-ripple artwork, frosted surfaces, a Mincho/geometric font pairing and a short reduced-motion-aware reveal. Opaque fallbacks and reduced-transparency preference are included. Uploaded wallpapers remain available. The intro now runs while the local engine starts instead of showing an extra opening-lessons explanation page. Native-to-web elapsed/skip state prevents replay and preserves the existing total animation duration; startup retry controls remain available.

All 210 regression/interaction checks passed: 6 intro handoff, 28 navigation/theme, 23 kanji/theme/display (including logo invariance), 14 overlay-scroll, 8 timed-mock, 11 cloud/offline DOM, 13 audio lifecycle, 28 simulated-cloud/offline, 13 number/startup, 16 search, 15 safety, 5 full-content, 8 voice-search, 20 map and 2 speaking checks. The final compiled AAB also passed 6,971 GET requests plus POST/backup/repeated-server smoke checks. Signed Android release build, lint (0 errors/27 warnings), signature, bundle validation, preserved certificate, 16 KB ELF/ZIP alignment and payload equality passed.

Physical-phone font/layout, actual glass rendering/scroll performance and native audio/permission checks remain pending. Firebase configuration remains disabled and needs publisher configuration and live verification. This build is an internal-testing candidate.


## Section rendering, classic fonts and logo — build 27

Kanji and Everyday initially display 96 entries. Show more appends the next batch; search and category/level filters cover the entire immutable public metadata catalog. Kanji Back restores the loaded range, selected character, level, query and scroll. Exact word links from global search open entries beyond the initial batch. Versioned public assets receive long cache lifetimes, while HTML pages and learner APIs remain no-store. Shared/page scripts load with defer, preserving dependency order; the early theme script remains immediate. Android retires older service workers because its lesson/assets are already bundled offline. Browser offline caching remains available. Repeated list-card backdrop blur is removed; floating glass chrome remains.

The previous classic Source Serif 4 / Japanese Mincho font style is bundled offline and restored for all seven skins. The existing icon uses a fixed matching navy frame with cream lettering in the header/opening, independent of the theme. Water Glass and other palettes/icons remain.

All 226 regression/interaction checks passed, including 10 catalog batch/deep-link, 3 asset-cache/loading and 3 browser-cache routing checks, plus the earlier 210 checks rerun for this build. The final compiled AAB passed 6,971 page/API GETs and POST/backup/repeated-server smoke checks. Signed release build, lint (0 errors/27 warnings), signatures, preserved certificate, bundle validation, 16 KB native/ZIP alignment and matching APK/AAB payloads passed.

Desktop generation measurements (five requests per route): Kanji payload 830,778 to 198,070 bytes; median generation 33.35 to 3.1 ms. Everyday payload 2,220,487 to 1,125,673 bytes; median generation 54.88 to 3.93 ms. These are desktop checks, not phone rendering-time measurements. Current packaged checks include restored serif fonts and full catalog browsing.

Physical phone rendering, scroll performance, large-text layout, upgrade and native audio/permission checks remain pending. Firebase configuration is still disabled pending publisher setup and live verification. This is an internal-testing candidate.


## Current design update — build 28, 10 October 2026

Sakura Journey is the default light appearance; Follow device appearance uses Kyoto Night in dark mode. Water Glass is also featured. Six other palettes and explicit saved preferences remain available. The dashboard has a compact original vector landscape, clear Continue learning action, actual progress, next chapter previews and consistently shaped icons. The logo, offline classic fonts, all content and learning functions remain. No additional permission, external asset or background animation was introduced.

- 234 regression checks passed across 19 Python/JavaScript suites. A separate smoke test passed 6,971 GET page/API requests and the POST, backup and repeat-server scenarios using compiled Python extracted from the signed AAB.
- Desktop Chromium passed 75 layouts across the three featured themes at 320, 390, 600 and 1180 pixels, including enlarged-text checks on Home. Ten browser interactions passed, including daily goal, preference persistence, N4 Back context and timed-mock selection. Screens had no JavaScript errors or failed requests. Browser screenshots show the implemented interface; they are not physical-device screenshots.
- Signed APK/AAB built successfully. Release lint: 0 errors, 26 warnings. Bundletool validation, signatures, upload-certificate preservation, native 16 KB ELF/ZIP/bundle alignment and APK/AAB payload equality passed. Every compiled module and packaged asset matches final source. All 21 public learning JSON files are unchanged.

Physical Android and Play internal-track testing, native font scaling and other production tasks listed above remain pending. Firebase remains disabled until configured and verified.


## First-launch setup and kanji notifications — build 30, 10 October 2026

The five starting-point choices are marked seen on their first appearance, including placement/skip/leaving without a choice. Existing onboarding preferences survive upgrades. The upper Kotoba header hides only while setup is open and returns afterward. The version remains 1.0.0; internal version code is 30.

Settings → Kanji notification & lock screen, or Show this kanji in a notification on a kanji detail, opens the new optional feature. Choose N5–N1, a whole level or selected ordered kanji; rotate every 15–1440 minutes; show a single card for 1–1440 minutes; or keep it until Next/Stop. Meaning and on-/kun-readings can be hidden. The native notification works offline without running the lesson server, has Next/Stop actions, and opens the exact kanji. Settings persist across relaunch; boot/upgrade restores active notifications and their remaining duration. It is off by default and requires notification permission. Notification settings and selections stay on this device.

The full card can appear in the notification shade and lock screen if Android allows it. The kanji also becomes a monochrome notification icon for compatible always-on displays. Full AOD text and placement beneath time/date depend on the phone; the app cannot override system AOD layout. Non-wakeup inexact alarms allow Android to defer background rotation; single-card expiry uses the system notification timeout on API 26+. No overlay, exact-alarm, foreground-service or battery-exemption permission was added.

- 274 regression checks passed: 264 Python/DOM checks across 22 suites and 10 native Kotlin timing/selection unit tests. The final compiled AAB passed 6,973 GET page/API requests plus POST, backup and repeated-server checks.
- Desktop Chromium passed 24 layouts: nine onboarding scenarios, twelve notification settings scenarios and three enlarged-text checks. Selection, custom duration, activation, hold and stop passed with a simulated native bridge; no page errors. These do not verify actual Android notifications.
- Signed APK/AAB, release lint (0 errors, 32 warnings), signatures, preserved upload certificate, bundle validation, 16 KB ELF/ZIP/bundle alignment and equal Python/Dex payloads passed. All Python modules, assets and native notification catalog match source. All 21 public learning JSON files are unchanged. Six additional lint warnings suggest optional KTX syntax.

Before production, test first install/kill/reopen/upgrade setup behavior on a real phone. Test notification permission allowed/denied, blocked channels, lock screen privacy settings, AOD icon rendering, Next/Stop/dismissal, exact-kanji opening cold/warm, single-card expiry, Doze delays, reboot and upgrade. Confirm no sound or unwanted wakeups at default channel settings. Physical Android, Play internal track and the other production tasks above remain pending.

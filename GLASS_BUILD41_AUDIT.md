# Build 41 glass/audit fixes

Source: build 40. Presentation and asset version only; no learner data, routes, or speaking content changed.

## Issues from screenshots
- Hiragana kana modal: one frosted dialog; the full-screen scrim no longer acts as a second heavy opaque plate.
- Hiragana flashcards: apply backdrop sampling to `.flash-face`, not the empty parent, and keep navigation buttons translucent.
- Japan Explorer: add glass to the four `.japan-how > div` instruction tiles and unstyled map/side-list/passport surfaces; leave map geography and interactive controls sharp.
- Refraction: isolate and restrain it to the home hero; remove overlapping displacement layers from other cards and never filter the global header, footer, text, or map.
- Accessibility: lite and reduced-transparency variants; preserve correct/incorrect and selected states.
- Cache: static asset build 41 and offline worker cache 41, Android source mirrored.

## Testing
- `python test_glass_surface_41.py` verifies source selectors, version, data neutrality, and Android mirror.
- Browser fixture tests at desktop/mobile sizes inspect computed styles and overflow for kana modal, flashcard face, Japan Explorer panels, and sticky navigation.
- Complete Android APK and physical device GPU performance still require GitHub Actions/device testing.

## Additional regression caught in browser testing
- The `.flash-mode` and `.flashcard` wrappers were still getting a higher-specificity background from the broad `:is()` selector, creating a flat square behind the frosted flashcard. Explicitly clear only those nonvisual wrappers; the actual `.flash-face` retains its rounded backdrop blur.
- The offline service worker's asset URL suffix was also updated from `?v=40` to `?v=41`, alongside the cache key and Flask asset build number.
- Chromium layout check completed at 320, 390, 430, 760, and 1365 CSS px, including working modal close/flashcard flip in a representative Kana fixture, Japan Explorer map/list/instruction panels, Settings dropdown scroll, and no horizontal overflow.

# Kotoba Liquid Glass UI (build 35)

A theme-aware, performance-conscious liquid-glass finish for the existing
immersive web/Android app shell. **App version stays 1.0.0.** No roadmap,
learning, review, notifications, speech, payment, or account logic changes.

## What changed

- Frosted translucent top bar and bottom navigation with a static light reflection.
- Soft glass capsules for Back and dashboard controls.
- Solid-enough, theme-aware card backgrounds to keep Japanese characters and
  answer text readable over user-uploaded photos and animated wallpapers.
- Answer cards keep their correct/wrong highlighting; tap effects use the
  existing delegated `ripple.js` handler.
- Glossy progress indicators with a subtle traveling highlight.
- Settings > Display > **Liquid glass finish** switch. On by default,
  remembers the choice only on the device via `kotoba:liquid-glass`.
- Performance safeguards: strong blur is limited to navigation shell;
  cards use simulated glass. WebView with <=3 GB reported device RAM gets
  a lighter effect. Reduced motion/transparency preferences are respected,
  and switching the finish off eliminates the added blur/shine.

## Implementation

- `static/css/liquid-glass.css` contains all non-destructive visual overrides.
- `static/js/liquid-glass.js` manages the visual preference; an early one-line
  preference restore in `templates/base.html` prevents flicker on navigation.
- The CSS and JS are mirrored under the Android Chaquopy package, and listed
  in the offline service worker. `ASSET_BUILD` and the service worker cache
  version are both `35` to invalidate old cached JavaScript/styles safely.
- `test_liquid_glass.cjs` verifies the toggle, low-memory behavior,
  accessibility styling and Android-bundle parity. Cache-routing tests no
  longer pin a specific asset version.

## Verify

On GitHub Actions, run the existing verify-and-build workflow. It executes
`test_liquid_glass.cjs`, the other CI regression tests, then Gradle builds the
Android debug APK. The full Gradle build still needs to complete there.

- Build 38: made Liquid Glass more background-reactive so header, footer, settings, and major cards pick up more color from wallpapers/themes while preserving readability.

# Liquid Glass integration (build 39)

The upstream `liquid-glass-react` package (Max Rovensky, MIT) is a React component with a displacement-map refraction effect. Kotoba is Flask/Jinja + vanilla JavaScript inside an Android WebView. Rather than adding a second React rendering tree over the existing interactive UI, the supplied library's standard displacement map and SVG filter technique were adapted directly into `static/js/liquid-glass.js` as native SVG + DOM layers. The original license accompanies the integration at `static/vendor/liquid-glass-react/LICENSE`. No network requests or new runtime packages are necessary.

The advanced effect is layered behind content in selected surfaces: header, bottom nav, settings, home hero, selected cards, modal, and speaking/review panels. CSS translucent blur remains as the fallback when URL filters or backdrop filters cannot be rendered. The `Liquid Glass` switch preserves its existing `kotoba:liquid-glass` storage key. Reduced transparency and low-memory modes use a simpler effect. It never modifies study logic or the learner database.

Theme simplification: the nine preset palettes became two foundations (Light / Sakura Journey and Dark / Kyoto Night) with automatic device appearance. Old selections map to the nearest supported mode. Custom wallpaper upload/cropping and dim strength are retained. Other decorative preset SVGs were removed.

Validation: run `node --check static/js/liquid-glass.js`, `python -m unittest test_glass_integration.py`, and standard app tests. Android APK rendering/performance should additionally be checked on physical devices.

## Build 42 safety note
The experimental SVG displacement-refraction layer is no longer active in the app due to repeated square compositor artifacts in desktop Chromium and Android WebView. The MIT attribution is preserved; Kotoba now uses native wallpaper-reactive backdrop blur with a single rounded surface per visible panel. See `GLASS_BUILD42_AUDIT.md`.

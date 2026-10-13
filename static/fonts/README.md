# Offline theme fonts

Rounded Mplus 1c Regular and Shippori Mincho Regular are bundled in WOFF2 form, converted without removing glyphs from the official Google Fonts TTF distributions. Original copyright and SIL Open Font License notices accompany each font.

Sources:
- https://github.com/google/fonts/tree/main/ofl/roundedmplus1c
- https://github.com/google/fonts/tree/main/ofl/shipporimincho

Font display uses swap so lessons remain accessible while a local face loads. No remote font service is contacted by the app. Themes combine these faces with platform sans/monospace stacks. Japanese reference text and meanings are not changed by a skin.

Nunito Sans (variable, upright) and Space Grotesk (variable) are also bundled as WOFF2 for readable UI text and real font weights. Full source fonts were converted without glyph subsetting; their OFL notices are included. Sources: https://github.com/google/fonts/tree/main/ofl/nunitosans and https://github.com/google/fonts/tree/main/ofl/spacegrotesk . No font is fetched at runtime.

`kotoba-brand.woff2` is a small Shippori Mincho subset for the same opening logo lettering before the lesson server starts. Its internal family is renamed Kotoba Brand; the Shippori Mincho OFL notice applies. The full Japanese fonts remain bundled for lessons.

Build 27 restores the earlier serif UI: Source Serif 4 (full variable WOFF2, sourceserif4-OFL.txt) and Japanese Mincho. Kotoba Brand Latin is a renamed subset of Source Serif 4 for the native intro; its original OFL applies.
